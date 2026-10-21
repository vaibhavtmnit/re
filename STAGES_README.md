# SFTR validation library: stages and data transformations

This document defines the stages of building a validation library: what each stage does, what it consumes, what it produces, and how its output is checked. It does not yet choose specific models, agent frameworks, or implementation tools.

The main object moving through the system is a **requirement with its evidence**, gradually becoming an executable validation. A field combination alone is not evidence that a validation should exist.

The worked example is fictional. It illustrates the pipeline and is **not an SFTR requirement**.

## Contents

- [1. Find and extract requirements](#1-find-and-extract-requirements)
- [2. Convert evidence into executable rules](#2-convert-evidence-into-executable-rules)
- [3. Test, release, and maintain the library](#3-test-release-and-maintain-the-library)
- [4. Worked example: intermediate data transformations](#4-worked-example-intermediate-data-transformations)
- [5. Attributes required for every stage](#5-attributes-required-for-every-stage)
- [6. Feedback paths between stages](#6-feedback-paths-between-stages)

## 1. Find and extract requirements

| Stage | Role | Input → output | Who does the work? | Completion check |
|---|---|---|---|---|
| **1. Define the target** | Establish which reporting regime, version, report types, dates, and repository the library must support. | Project requirements → **scope specification** | Developer with domain reviewer | Applicability can be decided explicitly; unresolved scope is recorded. |
| **2. Build the source inventory** | Identify which sources can supply field definitions, validation rules, exceptions, examples, and operational requirements. | Scope → **source catalogue** | Research agent, verified by reviewer | Each source has an owner, purpose, authority, version, and acquisition status. Missing sources remain visible. |
| **3. Acquire and freeze sources** | Obtain reproducible copies and preserve their identity. | Source catalogue → **versioned source collection** | Deterministic acquisition tools | Every acquired file has a hash, retrieval date, original location, and version metadata. Failed downloads are recorded. |
| **4. Recover document structure** | Extract tables, paragraphs, footnotes, headings, formulas, and references while preserving their relationships. | Source files → **structured document blocks** | Parsers; visual/OCR assistance where needed | Blocks retain exact source locations. Unreadable cells, broken tables, and uncertain ordering are flagged. |
| **5. Build the field dictionary** | Establish stable identities for fields and their meanings. | Definitions, schemas, and tables → **field registry** | Structured extraction plus AI for ambiguous mappings | Every field has its namespace, identifier, type, allowed values, units, cardinality, and applicability where available. Ambiguous aliases are unresolved, not guessed. |
| **6. Find requirement-bearing material** | Identify passages that express requirements, prohibitions, exceptions, dependencies, or definitions that affect validation. | Document blocks → **candidate evidence units** | Explicit-rule importers plus an LLM extraction pass | Every block has a processing status. Excluded blocks have reasons; a sample is independently checked for missed requirements. |
| **7. Assemble complete evidence packets** | Attach the context needed to interpret each candidate correctly. | Candidate units + document links → **evidence packets** | Reference resolver plus an agent for difficult references | Relevant headings, table headers, definitions, footnotes, exceptions, and referenced passages are attached—or explicitly missing. |

Stages 6 and 7 are separate because identifying a sentence is different from understanding its complete scope. “Field C must be populated” may be misleading without the heading “For transaction type X only.”

## 2. Convert evidence into executable rules

| Stage | Role | Input → output | Who does the work? | Completion check |
|---|---|---|---|---|
| **8. Extract atomic requirements** | Express each independently testable obligation without losing its conditions or exceptions. | Evidence packets → **structured requirement records** | LLM, with deterministic schema checks | Each record identifies applicability, condition, required outcome, exceptions, and supporting evidence. Missing information is marked explicitly. |
| **9. Bind terms to fields and values** | Replace textual references with exact field identifiers and typed values. | Requirement records + field registry → **bound requirements** | Deterministic matching; AI proposes uncertain mappings | Every referenced field, code, unit, and date concept resolves uniquely. Unresolved mappings block compilation. |
| **10. Reconcile overlapping requirements** | Identify duplicates, amendments, contradictions, and requirements that apply to different contexts. | Bound requirements + source metadata → **reconciled requirement set** | Comparison tools plus targeted domain review | Conflicts have an explicit resolution or remain blocked. Similar wording alone does not justify merging. |
| **11. Formalise the logic** | Translate requirements into a restricted, executable rule language. | Reconciled requirements → **typed rule expressions** | Compiler; LLM can propose expressions | Expressions use supported operators and define missing-value, repeated-record, time, and applicability semantics. |
| **12. Analyse constraints** | Detect impossible conditions, incompatible rules, redundant rules, and useful logical consequences. | Rule expressions + field domains → **analysis findings and derived candidates** | Constraint solver and static analysis | Findings identify the exact assumptions and supporting rules. Derived candidates remain separate from source requirements. |
| **13. Adjudicate unresolved issues** | Resolve ambiguities that automation cannot safely settle. | Ambiguities, conflicts, counterexamples → **decisions or blocked rules** | Domain reviewer, assisted by evidence retrieval | Each decision records its rationale and evidence. An AI confidence score does not resolve a regulatory ambiguity. |

Stage 12 cannot discover an obligation absent from the evidence. It can discover that existing obligations imply another condition, or reveal a gap requiring further source investigation.

## 3. Test, release, and maintain the library

| Stage | Role | Input → output | Who does the work? | Completion check |
|---|---|---|---|---|
| **14. Construct independent test expectations** | Establish what correct behaviour should be, using source examples, reviewed interpretations, and relevant reporting feedback where available. | Evidence + reviewed requirements → **reference cases with expected outcomes** | Independent reviewer or separate extraction process | Expected outcomes are traceable to evidence rather than generated solely from the executable rule. |
| **15. Generate challenging cases and test** | Exercise boundaries, exceptions, missing values, interacting rules, repeated records, and lifecycle scenarios. | Rules + reference cases → **test cases and results** | Test generators, solver, Python test runner | Reference cases pass; failures are triaged; mutation tests show that meaningful rule mistakes are detected. |
| **16. Assess coverage and package a release** | Decide exactly what the library supports and publish a reproducible version. | Rules + evidence + tests + unresolved items → **versioned validation package and coverage report** | Automated release checks with accountable review | Supported scope, omitted requirements, blocked rules, dependencies, and test evidence are explicit. |
| **17. Validate reporting data** | Apply the released rules to records and required external context. | Reporting data + rule package + reference/state data → **validation results** | Deterministic Python runtime | Each result identifies the rule, affected data, evidence, and outcome: pass, fail, not applicable, or not evaluated. |
| **18. Process changes and feedback** | Update only the affected parts when sources, schemas, reference data, or reporting behaviour change. | New versions + operational feedback → **change-impact tasks** | Change detector plus targeted agents/review | Changed dependencies trigger re-extraction and retesting. Previous releases remain reproducible. |

The stages form a pipeline with explicit return paths. An unbound field in stage 9 returns to stage 5. A contradiction in stage 12 may return to stage 7 to recover a missing exception.

## 4. Worked example: intermediate data transformations

### Starting point: a fictional source requirement

> For NEW reports, if A is X and B is Y, C must be an integer from 2 through 23 inclusive. This requirement does not apply when E is EXEMPT.

### After stages 3–4: preserved source evidence

```json
{
  "source_id": "example-manual-v1",
  "location": "section 4, paragraph 12",
  "text": "For NEW reports, if A is X and B is Y, C must be an integer from 2 through 23 inclusive. This requirement does not apply when E is EXEMPT."
}
```

This object preserves what the source says. It does not yet contain our interpretation. Source identity, location, and text travel with subsequent artifacts so that a reviewer can trace a validation back to its evidence.

### After stage 5: field definitions

```text
report_type: enumeration containing NEW
A: enumeration containing X
B: enumeration containing Y
C: optional integer
E: enumeration containing EXEMPT
```

“Optional integer” means the underlying data structure permits absence. A conditional rule can still require it. These abbreviated definitions are illustrative; a real registry also records exact identifiers, domains, units, versions, and evidence.

### After stages 7–9: a bound requirement

```json
{
  "requirement_id": "REQ-001",
  "scope": {"report_type": "NEW"},
  "when": [
    {"field": "A", "equals": "X"},
    {"field": "B", "equals": "Y"}
  ],
  "unless": {"field": "E", "equals": "EXEMPT"},
  "must": {
    "field": "C",
    "present": true,
    "type": "integer",
    "minimum": 2,
    "maximum": 23,
    "bounds": "inclusive"
  },
  "evidence": ["example-manual-v1:section-4:paragraph-12"]
}
```

The evidence supports four details: report scope, trigger, exception, and required outcome. The `when` conditions are conjunctive in this illustrative format.

### After stage 11: executable meaning

```text
applicable =
    report_type == NEW
    AND A == X
    AND B == Y
    AND E != EXEMPT

required =
    C is present
    AND C is an integer
    AND 2 <= C <= 23

rule =
    applicable IMPLIES required
```

This is explanatory notation, not Python code. The runtime must implement the specified missing-value and type semantics instead of inheriting accidental behaviour from the programming language.

For this example:

- If applicability is true, a missing, non-integer, or out-of-range C fails the rule.
- If applicability is false, the rule is not applicable.
- If applicability cannot be determined, the rule is not evaluated.

If E is absent while the other trigger conditions are true, the system cannot automatically interpret that as “not exempt.” Applicability is unknown, producing `NOT_EVALUATED`. A separate completeness rule may also report the missing field.

### At stage 12: constraint analysis

Suppose another fictional requirement says:

```text
Under the same applicability conditions, D = 2 × C.
```

The solver can derive:

```text
Under those applicability conditions:
D belongs to {4, 6, 8, ..., 46}.
```

Merely deriving `4 <= D <= 46` loses the even-number restriction.

The derived condition must retain links to both supporting requirements. It is a consequence of those requirements, not a newly discovered regulatory obligation. Its applicability conditions must also be retained.

### At stages 14–15: test expectations

Unless a row overrides them, assume `report_type = NEW`, `A = X`, `B = Y`, and E has a known, valid, non-exempt value.

| Input variation | Expected result for REQ-001 |
|---|---|
| `C = 2` or `C = 23` | Pass |
| `C = 1` or `C = 24` | Fail |
| C missing | Fail |
| `C = 2.5` | Fail |
| `E = EXEMPT` | Not applicable |
| E missing | Not evaluated |
| A has a known, valid value other than X | Not applicable |

These are outcomes for this rule, not a declaration that the whole report is valid.

Testing should also deliberately remove the exception or change `<= 23` to `< 23`. The tests should catch both mistakes. This checks whether the tests can detect meaningful defects, rather than merely execute the code.

## 5. Attributes required for every stage

Each stage needs an operational contract in addition to its role and input/output.

| Attribute | What it records | Why it matters |
|---|---|---|
| **Dependencies** | Source versions and upstream artifacts used. | Allows reproducibility and targeted updates. |
| **Failure behaviour** | Whether to retry, request missing evidence, send for review, or block downstream work. | Prevents silent failures and unsupported rules reaching release. |
| **Uncertainty** | The specific extraction, mapping, or interpretation that remains uncertain. | Makes review actionable instead of relying on one overall confidence score. |
| **Reprocessing unit** | One document block, field, requirement, or dependency group. | Avoids repeating the entire pipeline after a small change. |
| **Measurements** | Processing time, model tokens, review minutes, failure rate, and independently measured error rate. | Reveals actual cost, efficiency, and quality bottlenecks. |
| **Completion evidence** | The checks that justify accepting the output. | Gives downstream stages a clear acceptance contract. |

These measurements allow resource estimates to be based on a pilot rather than assumed model performance. Quality measurements must state their denominator and how the reference answers were established.

## 6. Feedback paths between stages

The stage numbers show the main flow, but unresolved findings return to the stage that can repair them.

| Finding | Return to | Required action |
|---|---|---|
| A required source is unavailable. | Stage 2 or 3 | Record the coverage gap and acquire the source when possible. |
| A table header or footnote is missing. | Stage 4 or 7 | Repair extraction or attach the missing context. |
| A field name maps to multiple identifiers. | Stage 5 or 9 | Resolve the identity using definitions and applicability. |
| Two requirements appear to contradict each other. | Stage 7, 10, or 13 | Check scope, exceptions, amendments, and source authority before resolving. |
| A rule trigger is impossible. | Stage 9, 11, or 13 | Check field binding and translation; determine whether the source requirement is genuinely unreachable. |
| A reference test disagrees with the compiled rule. | Stage 8, 11, or 14 | Inspect both the interpretation and the expected result against source evidence. |
| A source changes. | Stage 18, then affected stages | Follow recorded dependencies, rebuild affected artifacts, and rerun relevant tests. |

This document defines the stage boundaries. Detailed source selection, algorithms, model assignments, implementation choices, and measured resource estimates can be developed within those boundaries.
