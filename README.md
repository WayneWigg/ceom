# Control Evidence Object Model

A record model for what an AI agent is permitted to do, what it is expected to
do, what it was observed doing, and the evidence for each.

**Published at <https://ceom.aiscale.ltd>**

| | |
|---|---|
| **This version** | [10.5281/zenodo.23687472](https://doi.org/10.5281/zenodo.23687472) — cite this |
| **Current version** | [10.5281/zenodo.23687471](https://doi.org/10.5281/zenodo.23687471) — always the latest |

## What problem it addresses

Permissions for AI agents are well served by existing standards. Scopes, rich
authorisation requests, token exchange and authorisation APIs all describe what
an agent may do. **Observed actions and the evidence for them have no common
schema.** The consequence is that an organisation can hold a register, a
policy, a committee and a risk assessment process and still be unable to state
whether what its agents did matches what anyone intended.

This model records that layer. Twelve objects across four layers, from an
obligation through to the evidence for it, holding three positions on every
action rather than two: what the grants permit, what the accountable person
expects, and what was observed. The divergence between the second and the third
is where authority expands without anyone deciding that it should.

## This version

| | |
|---|---|
| Version | 0.9.10, pre-1.0 |
| Specification | [PDF](0.9.10/control-evidence-object-model-v0.9.10.pdf) &middot; [source](0.9.10/control-evidence-object-model-v0.9.10.md) |
| JSON Schema | [`ceom.schema.json`](0.9.10/ceom.schema.json) (draft 2020-12) |
| Field dictionary | [`ceom.field-dictionary.csv`](0.9.10/ceom.field-dictionary.csv) |
| Vocabularies | [`ceom.vocabularies.json`](0.9.10/ceom.vocabularies.json) |
| Reference validator | [`reference/`](0.9.10/reference/) |

## The twelve objects

| Layer | | |
|---|---|---|
| Designed | 1 Obligation | a discrete requirement from a source |
| | 2 Interpretation | the organisation's position on it |
| | 3 Control | what is done about it |
| | 4 Owner | standing accountability for a thing |
| | 5 Authority | what a role may do, and who approved that |
| Estate | 6 Asset | a thing that exists and can be referenced |
| | 7 Dependency | an edge between assets |
| Runtime | 8 Action | an act, in one of three modes |
| | 9 Exception | a recorded divergence |
| | 10 Decision | a determination somebody is answerable for |
| Spanning | 11 Evidence | what was examined, and how completely |
| | 12 Permission | a grant that crosses an organisational boundary |

## Conformance

Annex D of the specification states what conformance means and distinguishes
two kinds of failure that must never be mixed. **A defect means the records are
malformed**, so nothing can be concluded from them. **A finding means the
records are well formed and say something about the subject.** A null approver
is not a broken record; it is a statement that nobody approved the grant.

**Conformance is the absence of defects. It is not the absence of findings.**

The reference validator implements rules C1 to C13 and prints, with each
result, the sentence from the specification that it enforces.

## Identifiers

Terms are identified under this namespace, versioned:

    https://ceom.aiscale.ltd/0.9.10/object/obligation
    https://ceom.aiscale.ltd/0.9.10/field/obligation.source_ref
    https://ceom.aiscale.ltd/0.9.10/term/exception/transformation_defect

These are names. Only the schema resolves to a document today; the remaining
term addresses are identifiers rather than endpoints, and will be served when
there is a reason to.

## Licensing

| What | Licence |
|---|---|
| Specification, field dictionary, vocabularies | [CC BY 4.0](0.9.10/LICENSE-CC-BY-4.0.txt) |
| JSON Schema, reference validator | [Apache 2.0](0.9.10/LICENSE-Apache-2.0.txt) |

Commercial implementation is permitted. Attribution is required.

## Citation

> Wiggins, W. (2026). *Control Evidence Object Model, version 0.9.10.*
> AIscale Ltd. DOI 10.5281/zenodo.23687472

## Status, stated plainly

The twelve objects, the four layers, the evidence scale, the reference states
and the gap scale are stable. Field-level detail may still move.

The model has been instantiated against two real agent assessments. **The
worked examples in the specification are constructed, deliberately**, so that
no reader receives a client estate along with the document.

**What it still lacks is the measurement that matters:** two assessors reaching
the same determinations independently from the same artefacts. Read Annex D
section D.1 before claiming conformance.

## What is not here

The assessment practice built on this model, including report formats, the
scenario method and the position library, is not published and is not required
in order to implement the model. No client material or engagement data is in
this repository.

## Contributing

Challenge and correction are both wanted. The model was circulated for
challenge rather than adoption. **Open question 11 in the specification is the
one that most needs other people:** whether the Exception vocabulary survives
contact with the parties who must map into it. Ten terms, each of which
somebody's existing classification must fold into without loss.

Open an issue.
