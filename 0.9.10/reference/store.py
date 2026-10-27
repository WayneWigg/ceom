"""The record store.

Until now an engagement's object graph has been a Python source file typed by
hand. That is why a wrong asset reference could be carried forward unnoticed,
why two engagements could use two vocabularies for one boolean, and why a
correct finding could be overwritten by a tidier later draft. All three were
bookkeeping failures rather than failures of understanding, and none of them is
fixed by a better reader.

This store fixes them by construction:

  * Every record carries the artefact and locator it came from, and **how** it
    was obtained: parsed, read or asserted.
  * Every record carries a confirmation state. Nothing is confirmed by being
    written down. A person confirms it, and the store records who and when.
  * **Nothing is ever overwritten.** A change inserts a new version and marks
    the previous one superseded. The history is the point.

Shape. One table of records rather than twelve, because the model is a graph
and tables are projections of it. Object-specific fields live in a JSON
payload, validated against the published field dictionary, so a model version
change does not require a migration.

Usage:
    from store import Store
    s = Store('ceom.db')
    s.open_engagement('demo', 'A constructed agent, for illustration')
    s.put('demo', 5, 'AUT-0001', {...}, source='AST-0001',
          locator='task-role.inline-policy.json#Statement[0]',
          method='parsed', by='parser')
    s.confirm('demo', 5, 'AUT-0001', by='the assessor',
              note='checked against the policy document')
"""
import io
import json
import os
import sqlite3
import csv
import datetime

METHODS = ('parsed', 'read', 'asserted')
STATES = ('candidate', 'confirmed', 'rejected')

SCHEMA = """
CREATE TABLE IF NOT EXISTS engagement (
    engagement_id   TEXT PRIMARY KEY,
    subject         TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    opened_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artefact (
    engagement_id   TEXT NOT NULL,
    register_id     TEXT NOT NULL,
    artefact        TEXT,
    kind            TEXT,
    owned_by        TEXT,
    read_on         TEXT,
    corroborates    TEXT,
    sha256          TEXT,
    notes           TEXT,
    PRIMARY KEY (engagement_id, register_id)
);

CREATE TABLE IF NOT EXISTS record (
    row_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id   TEXT NOT NULL,
    object_number   INTEGER NOT NULL,
    record_id       TEXT NOT NULL,
    version         INTEGER NOT NULL,
    fields_json     TEXT NOT NULL,

    -- provenance: where it came from and how
    source_artefact TEXT,
    source_locator  TEXT,
    extraction      TEXT NOT NULL CHECK (extraction IN ('parsed','read','asserted')),
    extracted_by    TEXT,
    extracted_at    TEXT NOT NULL,

    -- attestation: who stands behind it
    state           TEXT NOT NULL CHECK (state IN ('candidate','confirmed','rejected')),
    state_by        TEXT,
    state_at        TEXT,
    state_note      TEXT,

    -- history: never overwrite
    supersedes      INTEGER,
    superseded_by   INTEGER,
    UNIQUE (engagement_id, object_number, record_id, version)
);

CREATE INDEX IF NOT EXISTS record_current
    ON record (engagement_id, object_number, record_id, superseded_by);

CREATE VIEW IF NOT EXISTS current AS
    SELECT * FROM record WHERE superseded_by IS NULL AND state <> 'rejected';
"""


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


class Store(object):

    def __init__(self, path, dictionary=None):
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.fields = self._load_dictionary(dictionary) if dictionary else {}

    # ------------------------------------------------------------- dictionary
    @staticmethod
    def _load_dictionary(path):
        """Field names and reference flags, per object, from the published
        dictionary. Used to reject a field the model does not define, which is
        how the inconsistent-boolean class of error is caught at the door."""
        out = {}
        with io.open(path, encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                n = int(row['object_number'])
                o = out.setdefault(n, {'name': row['object'], 'fields': {},
                                       'references': set()})
                o['fields'][row['field']] = row['definition']
                if row['is_reference'] == 'yes':
                    o['references'].add(row['field'])
        return out

    def unknown_fields(self, object_number, fields):
        """Fields not defined for this object. Empty tuple when the dictionary
        has not been supplied, because silence is not a pass."""
        if not self.fields:
            return ()
        known = set(self.fields.get(object_number, {}).get('fields', ()))
        # the assessment carries four derived columns alongside the model's own
        known |= {'Evidence state', 'Tier 1 state', 'Source artefacts', 'Notes'}
        known |= {'%s_id' % self.fields[object_number]['name'].lower()}
        return tuple(sorted(set(fields) - known))

    # ------------------------------------------------------------- engagement
    def open_engagement(self, engagement_id, subject, model_version='0.9.10'):
        self.db.execute(
            'INSERT OR REPLACE INTO engagement VALUES (?,?,?,?)',
            (engagement_id, subject, model_version, _now()))
        self.db.commit()

    def put_artefact(self, engagement_id, reg):
        self.db.execute(
            'INSERT OR REPLACE INTO artefact '
            '(engagement_id, register_id, artefact, kind, owned_by, read_on, '
            ' corroborates, sha256, notes) VALUES (?,?,?,?,?,?,?,?,?)',
            (engagement_id, reg.get('Register ID'), reg.get('Artefact'),
             reg.get('Kind'), reg.get('Owned by'), reg.get('Read on'),
             reg.get('Counted as corroboration'), reg.get('sha256'),
             reg.get('Notes')))
        self.db.commit()

    # ----------------------------------------------------------------- writes
    def current_row(self, engagement_id, object_number, record_id):
        return self.db.execute(
            'SELECT * FROM record WHERE engagement_id=? AND object_number=? '
            'AND record_id=? AND superseded_by IS NULL',
            (engagement_id, object_number, record_id)).fetchone()

    def put(self, engagement_id, object_number, record_id, fields,
            source=None, locator=None, method='read', by=None, note=None):
        """Insert a record, or supersede the current version with a new one.

        An unchanged payload is not reinserted, so re-running a loader is
        idempotent and does not manufacture a history that did not happen.
        """
        if method not in METHODS:
            raise ValueError('extraction must be one of %s' % (METHODS,))
        # A locator is what makes a claim checkable in seconds rather than by
        # rereading a document. A parser always knows the file and the position
        # it read from, so a parsed record without one is a defect in the
        # parser. A person reading prose should supply one and sometimes will
        # not, so that is permitted and counted rather than refused. An
        # asserted record is the assessor's own claim and has no locator by
        # definition, so it must instead say what it rests on.
        if method == 'parsed' and not (locator or '').strip():
            raise ValueError(
                'a parsed record must carry a locator: %s/%s' % (object_number, record_id))
        if method == 'asserted' and not (note or '').strip():
            raise ValueError(
                'an asserted record must carry a note saying what it rests on: '
                '%s/%s' % (object_number, record_id))
        payload = json.dumps(fields, sort_keys=True, ensure_ascii=False)
        cur = self.current_row(engagement_id, object_number, record_id)
        if cur is not None and cur['fields_json'] == payload \
                and cur['source_artefact'] == source \
                and cur['extraction'] == method:
            return cur['row_id'], False

        version = (cur['version'] + 1) if cur else 1
        c = self.db.execute(
            'INSERT INTO record (engagement_id, object_number, record_id, '
            'version, fields_json, source_artefact, source_locator, '
            'extraction, extracted_by, extracted_at, state, state_note, '
            'supersedes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (engagement_id, object_number, record_id, version, payload,
             source, locator, method, by, _now(), 'candidate', note,
             cur['row_id'] if cur else None))
        if cur is not None:
            self.db.execute('UPDATE record SET superseded_by=? WHERE row_id=?',
                            (c.lastrowid, cur['row_id']))
        self.db.commit()
        return c.lastrowid, True

    def set_state(self, engagement_id, object_number, record_id, state,
                  by=None, note=None):
        """Confirm or reject the current version. Confirmation is an act by a
        person and is never a side effect of writing a record."""
        if state not in STATES:
            raise ValueError('state must be one of %s' % (STATES,))
        cur = self.current_row(engagement_id, object_number, record_id)
        if cur is None:
            raise KeyError('%s/%s has no current version' % (object_number, record_id))
        self.db.execute(
            'UPDATE record SET state=?, state_by=?, state_at=?, state_note=? '
            'WHERE row_id=?', (state, by, _now(), note, cur['row_id']))
        self.db.commit()

    def confirm(self, engagement_id, object_number, record_id, by, note=None):
        self.set_state(engagement_id, object_number, record_id, 'confirmed',
                       by=by, note=note)

    # ------------------------------------------------------------------ reads
    def records(self, engagement_id, object_number=None, include_history=False):
        q = 'SELECT * FROM %s WHERE engagement_id=?' % (
            'record' if include_history else 'current')
        a = [engagement_id]
        if object_number is not None:
            q += ' AND object_number=?'
            a.append(object_number)
        return [dict(r, fields=json.loads(r['fields_json']))
                for r in self.db.execute(q + ' ORDER BY object_number, record_id, version', a)]

    def history(self, engagement_id, object_number, record_id):
        return [dict(r, fields=json.loads(r['fields_json']))
                for r in self.db.execute(
                    'SELECT * FROM record WHERE engagement_id=? AND '
                    'object_number=? AND record_id=? ORDER BY version',
                    (engagement_id, object_number, record_id))]

    def without_locator(self, engagement_id):
        """Records nobody can check quickly. Counted rather than hidden, on the
        same principle as SILENT and UNKNOWN never being collapsed."""
        return self.db.execute(
            "SELECT COUNT(*) FROM current WHERE engagement_id=? AND extraction<>'asserted' "
            "AND (source_locator IS NULL OR source_locator='')",
            (engagement_id,)).fetchone()[0]

    def profile(self, engagement_id):
        """Counts that say what the store knows and what anybody stands behind."""
        rows = self.db.execute(
            'SELECT object_number, extraction, state, COUNT(*) n FROM current '
            'WHERE engagement_id=? GROUP BY 1,2,3', (engagement_id,)).fetchall()
        out = {}
        for r in rows:
            o = out.setdefault(r['object_number'], {'total': 0, 'method': {}, 'state': {}})
            o['total'] += r['n']
            o['method'][r['extraction']] = o['method'].get(r['extraction'], 0) + r['n']
            o['state'][r['state']] = o['state'].get(r['state'], 0) + r['n']
        return out

    def close(self):
        self.db.close()
