CONTROL EVIDENCE OBJECT MODEL, version 0.9.10
=============================================

A record model for what an AI agent is permitted to do, what it is expected to
do, what it was observed doing, and the evidence for each.

DOI 10.5281/zenodo.23687472
AIscale Ltd, 27 October 2026


WHAT PROBLEM IT ADDRESSES
-------------------------

Permissions for AI agents are well served by existing standards: scopes, rich
authorisation requests, token exchange and authorisation APIs all describe what
an agent may do. Observed actions and the evidence for them have no common
schema. The consequence is that an organisation can hold a register, a policy,
a committee and a risk assessment process and still be unable to state whether
what its agents did matches what anyone intended.

This model records that layer. It starts from an obligation and ends at
evidence, and it holds three positions on every action rather than two: what
the grants permit, what the accountable person expects, and what was observed.
The difference between the second and the third is where authority expands
without anyone deciding that it should.


WHAT IS IN THIS DEPOSIT
-----------------------

  control-evidence-object-model-v0.9.10.md
  control-evidence-object-model-v0.9.10.pdf
      The specification, in source and typeset form. Twelve objects across
      four layers, the design principles, the evidence scale, the seven
      reference states, the gap scale, four annexes. Annex D states what
      conformance means.

  ceom-0.9.10-field-dictionary.csv
      Every field of every object: name, label, type, whether it is a
      reference, and what it means. The machine-readable companion to the
      field tables in the specification.

  ceom-0.9.10.vocabularies.json
      The controlled vocabularies, with the definition of every term.

  ceom-0.9.10.schema.json
      JSON Schema (draft 2020-12) for the twelve objects.

  reference/
      A reference validator implementing the conformance rules C1 to C13 of
      Annex D, with a record store that holds provenance and attestation
      state. Each rule prints the sentence from the specification that it
      enforces.

  LICENSE-CC-BY-4.0.txt     specification, dictionary, vocabularies
  LICENSE-Apache-2.0.txt    schema and reference implementation

  CHANGES-made-for-deposit.txt
      What was changed in the working sources to produce this published
      version, and why.


THE TWELVE OBJECTS
------------------

  DESIGNED   1 Obligation      a discrete requirement from a source
             2 Interpretation  the organisation's position on it
             3 Control         what is done about it
             4 Owner           standing accountability for a thing
             5 Authority       what a role may do, and who approved that

  ESTATE     6 Asset           a thing that exists and can be referenced
             7 Dependency      an edge between assets

  RUNTIME    8 Action          an act, in one of three modes
             9 Exception       a recorded divergence
            10 Decision        a determination somebody is answerable for

  SPANNING  11 Evidence        what was examined, and how completely
            12 Permission      a grant that crosses an organisational boundary


STATUS
------

Pre-1.0. The twelve objects, the four layers, the evidence scale, the
reference states and the gap scale are stable. Field-level detail may still
move. The model has been instantiated against two real agent assessments; the
worked examples in the specification are constructed, deliberately, so that no
reader receives a client estate along with the document.

What it still lacks is the measurement that matters: two assessors reaching
the same determinations independently from the same artefacts. That is stated
in the specification rather than hidden, and anyone implementing this model
should read Annex D section D.1 before claiming conformance.


WHAT IS NOT PUBLISHED
---------------------

The assessment practice built on this model, including report formats, the
scenario method and the position library, is not published and is not required
in order to implement the model. No client material, engagement data or
assessment output is included in this deposit.


CITATION
--------

  Wiggins, W. (2026). Control Evidence Object Model, version 0.9.10.
  AIscale Ltd. DOI 10.5281/zenodo.23687472

Challenge, correction and implementation reports are all welcome. The model
was circulated for challenge rather than adoption, and open question 11 in the
specification is the one that most needs other people: whether the Exception
vocabulary survives contact with the parties who must map into it.
