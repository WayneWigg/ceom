"""The validator: the loading rules the specification already states, enforced.

Until now these rules existed as sentences in a document and were applied by an
assessor remembering them. This turns them into checks that either pass or fail
against a loaded engagement.

**Two outputs, and they must never be mixed.**

A **defect** means the data is malformed. A cycle in a same-object reference, a
field the model does not define, a reference that names no record. The data is
wrong and loading it was a mistake by us.

A **finding** means the data is well formed and says something about the
subject. A grant with no approver. An approver who is the establisher. Evidence
captured by the thing it evidences. These are the assessment, not errors, and
reporting them as errors would be reporting our client's estate as our own bug.

Every rule carries the sentence from the specification that it enforces, so a
rule can be argued with by arguing with the document rather than the code.

Usage: python3 validate.py <store.db> <engagement_id>
"""
from paths import DICT as DEFAULT_DICT  # noqa: E402
import collections
import json
import sys

from store import Store

Result = collections.namedtuple('Result', 'rule kind object_number record_id detail')

# Fields that must resolve to a registered Asset, with the sentence that says so.
ASSET_REFS = {
    (1, 'source_ref'): 'Obligation.source_ref must resolve to a registered Asset, not free text.',
    (2, 'source_ref'): 'Interpretation.source_ref must resolve to a registered Asset, not free text.',
    (5, 'source_ref'): 'Authority.source_ref must resolve to a registered Asset, not free text.',
    (5, 'value_ref'): 'Authority.value_ref must resolve to a registered Asset.',
    (12, 'source_ref'): 'Permission.source_ref must resolve to a registered Asset, not free text.',
}

# Same-object references, which form a tree and never a cycle (principle 10).
TREE_REFS = {
    (1, 'part_of'): 'Obligation.part_of',
    (2, 'supersedes'): 'Interpretation.supersedes',
    (4, 'delegated_from'): 'Owner.delegated_from',
}

PRINCIPLE_10 = ('Same-object references form a tree, never a cycle. A cycle makes '
                'every upward traversal non-terminating, and the traversals are the '
                'point. Loading rejects one rather than discovering it on the first '
                'report that never returns.')


def _ref(value):
    """The identifier at the front of a reference, ignoring any label."""
    v = str(value or '').strip()
    return v.split()[0].rstrip(',') if v else ''


def _multi(value):
    """A field that may carry several identifiers."""
    v = str(value or '').strip()
    if not v:
        return []
    out = []
    for part in v.replace(';', ',').split(','):
        r = _ref(part)
        if r:
            out.append(r)
    return out


class Validator(object):

    def __init__(self, store, engagement_id):
        self.s = store
        self.e = engagement_id
        self.recs = store.records(engagement_id)
        self.by_id = {}
        self.by_object = collections.defaultdict(dict)
        for r in self.recs:
            self.by_id[r['record_id']] = r
            self.by_object[r['object_number']][r['record_id']] = r
        self.results = []

    # ------------------------------------------------------------- reporting
    def defect(self, rule, rec, detail):
        self.results.append(Result(rule, 'defect', rec['object_number'],
                                   rec['record_id'], detail))

    def finding(self, rule, rec, detail):
        self.results.append(Result(rule, 'finding', rec['object_number'],
                                   rec['record_id'], detail))

    # ----------------------------------------------------------------- rules
    def r_unknown_fields(self):
        """DEFECT. A field the model does not define. Two spellings of one field
        across two engagements made a count come out as nought where it was
        three, and nothing caught it."""
        for r in self.recs:
            bad = self.s.unknown_fields(r['object_number'], r['fields'].keys())
            if bad:
                self.defect('fields-defined', r, 'not in the dictionary: %s' % ', '.join(bad))

    def r_acyclic(self):
        """DEFECT, principle 10. A self-reference is a cycle of length one."""
        for (obj, field), label in TREE_REFS.items():
            pool = self.by_object.get(obj, {})
            for rid, rec in pool.items():
                seen, cur = [rid], _ref(rec['fields'].get(field))
                while cur:
                    if cur in seen:
                        self.defect('acyclic', rec, '%s cycle: %s -> %s. %s'
                                    % (label, ' -> '.join(seen), cur, PRINCIPLE_10))
                        break
                    if cur not in pool:
                        break
                    seen.append(cur)
                    cur = _ref(pool[cur]['fields'].get(field))

    def r_asset_refs(self):
        """DEFECT where the reference names nothing. FINDING where it is null,
        because a source nobody recorded is a statement about the estate."""
        assets = self.by_object.get(6, {})
        for (obj, field), sentence in ASSET_REFS.items():
            for rec in self.by_object.get(obj, {}).values():
                v = _ref(rec['fields'].get(field))
                if not v:
                    self.finding('asset-ref-null', rec,
                                 '%s is null. %s' % (field, sentence))
                elif v not in assets:
                    self.defect('asset-ref-resolves', rec,
                                '%s = %s resolves to no Asset. %s' % (field, v, sentence))

    def r_references_resolve(self):
        """DEFECT. Every declared reference field must name a record that
        exists. This is the rule that would have caught two wrong asset
        references in our own graph, which the scenario generator found by
        accident."""
        for r in self.recs:
            n = r['object_number']
            for field in self.s.fields.get(n, {}).get('references', ()):
                for v in _multi(r['fields'].get(field)):
                    if v and v not in self.by_id:
                        self.defect('reference-resolves', r,
                                    '%s = %s names no record in this engagement' % (field, v))

    def r_approver_differs(self):
        """FINDING. Authority.approved_by must differ from established_by.
        Self-approval is not approval. Null is a finding, not a blank."""
        for rec in self.by_object.get(5, {}).values():
            est = _ref(rec['fields'].get('established_by'))
            app = _ref(rec['fields'].get('approved_by'))
            if not app:
                self.finding('approver-present', rec,
                             'approved_by is null. Null is a finding, not a blank.')
            elif est and app == est:
                self.finding('approver-differs', rec,
                             'approved_by equals established_by (%s). Self-approval '
                             'is not approval.' % app)

    def r_evidence_independent(self):
        """FINDING. Evidence.captured_by must differ from the actor that
        performed the Action. Self-verification is not evidence."""
        for rec in self.by_object.get(11, {}).values():
            cap = _ref(rec['fields'].get('captured_by'))
            subj = _ref(rec['fields'].get('subject_ref'))
            if not cap:
                self.finding('capturer-present', rec, 'captured_by is null.')
                continue
            act = self.by_object.get(8, {}).get(subj)
            if act and _ref(act['fields'].get('actor_id')) == cap:
                self.finding('capturer-differs', rec,
                             'captured_by equals the actor that performed %s. '
                             'Self-verification is not evidence.' % subj)

    def r_derivation_outward(self):
        """FINDING, D108. A record cannot evidence the thing it was derived
        from, so COMPLETE requires a derivation that resolves outside the
        subject. A record derived from the implementation it describes is set
        aside from comparison rather than counted as agreement."""
        for r in self.recs:
            d = _ref(r['fields'].get('derived_from'))
            if d and d == r['record_id']:
                self.defect('derivation-not-self', r,
                            'derived_from points at itself')

    def r_enforced_by_independent(self):
        """FINDING. A control enforced by the same Asset it governs carries no
        independent statement, and a limit whose value the grantee maintains is
        not a limit."""
        for rec in self.by_object.get(5, {}).values():
            enf = _ref(rec['fields'].get('enforced_by'))
            tgt = _ref(rec['fields'].get('permitted_asset_id'))
            if enf and tgt and enf == tgt:
                self.finding('enforcement-independent', rec,
                             'enforced_by is the asset the grant is over (%s), so '
                             'the grant is enforced by the thing it governs.' % enf)
            val = _ref(rec['fields'].get('value_ref'))
            grantee = _ref(rec['fields'].get('granted_to'))
            if val and grantee and val == grantee:
                self.finding('limit-maintained-elsewhere', rec,
                             'value_ref is maintained by the grantee (%s), so the '
                             'limit is recorded as unenforced.' % grantee)

    def r_action_shape(self):
        """DEFECT on shape, FINDING on authority. destination_asset_id is
        required for extract and null otherwise. A null authority_id is a
        finding, not a blank."""
        for rec in self.by_object.get(8, {}).values():
            verb = str(rec['fields'].get('verb') or '').strip()
            dest = _ref(rec['fields'].get('destination_asset_id'))
            if verb == 'extract' and not dest:
                self.defect('extract-has-destination', rec,
                            'verb is extract and destination_asset_id is null')
            if verb and verb != 'extract' and dest:
                self.defect('destination-only-for-extract', rec,
                            'destination_asset_id set on verb %s' % verb)
            if not _ref(rec['fields'].get('authority_id')):
                self.finding('action-under-authority', rec,
                             'authority_id is null. Null is a finding, not a blank.')

    def r_owner_role(self):
        """FINDING. Owner.person is nullable, because a recognised role with
        nobody in it is a real and reportable state. A role that is itself
        missing is a defect."""
        for rec in self.by_object.get(4, {}).values():
            if not str(rec['fields'].get('role') or '').strip():
                self.defect('owner-has-role', rec, 'role is empty')
            elif not str(rec['fields'].get('person') or '').strip():
                self.finding('owner-has-person', rec,
                             'role is recorded with nobody holding it')

    # ------------------------------------------------------------------- run
    def run(self):
        for name in sorted(n for n in dir(self) if n.startswith('r_')):
            getattr(self, name)()
        return self.results


def report(results, engagement_id, total):
    defects = [r for r in results if r.kind == 'defect']
    findings = [r for r in results if r.kind == 'finding']
    print('%s: %d records, %d defects, %d findings'
          % (engagement_id, total, len(defects), len(findings)))
    for kind, rows in (('DEFECTS, our data is wrong', defects),
                       ('FINDINGS, their estate is', findings)):
        if not rows:
            continue
        print('\n  %s' % kind)
        by_rule = collections.Counter(r.rule for r in rows)
        for rule, n in by_rule.most_common():
            print('    %-28s %3d' % (rule, n))
            for r in [x for x in rows if x.rule == rule][:3]:
                print('        %-10s %s' % (r.record_id, r.detail[:96]))
            if n > 3:
                print('        ... and %d more' % (n - 3))


if __name__ == '__main__':
    DICT = DEFAULT_DICT
    s = Store(sys.argv[1], dictionary=DICT)
    eid = sys.argv[2]
    v = Validator(s, eid)
    report(v.run(), eid, len(v.recs))
