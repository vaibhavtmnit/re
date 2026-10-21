# Broader field selection and false-positive controls

The corpus covers the full field tables. Fields 2.3, 2.5, and 2.6 were starting examples, not the limit of the collection.

This file makes the broader experiment selection explicit and adds four reproducibly sampled fields. It is reviewer material; do not supply the control labels or invented-rule probes to the model during blind discovery.

**Selection: 52 unique fields — 46 main fields, four random supplementary fields, and two additional companion fields.**

## Main field groups

| Group | Selected fields | Investigation |
|---|---|---|
| Identity, dates, and lifecycle | 1.1, 1.3, 1.11; 2.1, 2.2, 2.3, 2.4, 2.12, 2.13, 2.14, 2.15, 2.98, 2.99 | Event chronology, reporting history, termination, and trade/position relationships. |
| Clearing | 2.5, 2.6, 2.7, 2.19 | Clearing model, timestamps, CCP identity, and Delivery by Value. |
| Collateral | 2.9, 2.20, 2.72, 2.73, 2.74, 2.75, 2.76, 2.77, 2.78, 2.95, 2.96 | Agreements, allocation, net exposure, component types, eligibility, and unknown baskets. |
| Rates | 2.23, 2.25, 2.32, 2.35, 2.36, 2.59 | Re-rating, future effective dates, and loan versus rebate rates. |
| Margin loans | 2.69, 2.71 | Outstanding exposure and transitions to or from zero. |
| CCP margin | 2.97; 3.4, 3.6, 3.7, 3.20 | Portfolio linkage, counterparties, and the margin-report lifecycle. |
| Reuse | 4.4, 4.7, 4.8, 4.9, 4.18 | Reporting identity, collateral instruments, reuse values, and aggregate lifecycle. |

These are investigation seeds, not a closed list of dependencies. Amounts, currencies, collateral components, or other fields needed by a particular scenario must still be brought into that scenario. The existing [16 investigations](SCENARIO_INDEX.md) supply the wider source locations.

## Random supplementary selection

Selection method: take Table 2 field numbers 1 through 99, exclude the Table 2 fields in the main groups above, sort the remaining numbers, and use Python `random.Random(20261021).sample(population, 4)` once. The draw was not repeated after seeing the result.

The draw returned **2.79, 2.10, 2.70, and 2.81**, in that order. The full population, seed, and selected IDs are saved in [field_selection.json](field_selection.json).

| Field | Name | Evidence in D04 | Companion context retained |
|---|---|---|---|
| 2.10 | Other master agreement type | L307-L319 | 2.9 and its other-agreement branch. |
| 2.70 | Base currency of outstanding margin loan | L609-L619 | 2.69 and 2.71; product applicability. |
| 2.79 | Classification of a security used as collateral | L639-L676 | Component type and the distinction between securities and commodities. |
| 2.81 | Sub-product | L663-L676 | 2.80 base product and 2.82 further sub-product; the classification table in D05. |

Definitions come from [D04](../documents/D04_rts_2019_356_original.txt), the [original adopted RTS](https://www.legislation.gov.uk/eur/2019/356/pdfs/eur_20190356_adopted_en.pdf). Formats and the classification table are in [D05](../documents/D05_its_2019_363_original.txt). These original EU texts still require the UK applicability and version checks documented in the main README.

Fields **2.80 and 2.82** are deliberately added companion fields, not extra random draws. They prevent testing 2.81 without its taxonomy context.

## Source input added

[Additional field passages](../experiment_inputs/additional_field_passages.txt) contains mechanically copied passages from D04 and D05, including surrounding definitions and the commodity classification table. It includes no expected outcomes, invented regulatory text, or negative-control labels.

It is a convenience extract of documents already collected, not a new independent source. Continue using the full documents when testing longer context. Fragment hashes and parent-source hashes are recorded in [additional_field_passages_manifest.json](../experiment_inputs/additional_field_passages_manifest.json).

## What counts as a false positive?

Two separate measurements are needed:

1. **Invented requirement:** the model asserts a regulatory dependency that its cited evidence does not support. A reviewer must distinguish an unsupported proposal from a demonstrated false statement. An unsupported proposal should not be promoted into a rule.
2. **Incorrect rejection:** the executable validator fails a record that an independent reviewer has established is valid for the tested scope and version.

Random selection alone establishes neither independence nor validity. All four sampled fields have their own legitimate context. They must remain eligible for real rules; we must not tell the model that they are universally irrelevant.

## Control investigations to prepare next

The claims in the second column are deliberately invented probes. **They are not regulatory requirements and must not be copied into the source corpus.** No executable tests or current-UK gold labels are claimed here.

| Control | Invented restriction or behaviour to probe | How to establish the expected outcome |
|---|---|---|
| FP-01: extra agreement name | A cleared trade must have a particular other-agreement name, inferred from a clearing example. | Review the agreement branch separately from the clearing rule. Seek evidence for the proposed extra condition; examples alone do not establish it. For a later record test, use reviewed valid agreement names and preserve all actual agreement requirements. |
| FP-02: currency hard-coding | Every margin loan reported in the UK must have GBP as its base currency. | Review product scope, currency format, and applicable UK requirements. Use independently approved non-GBP cases if permitted. Keep monetary amounts and their currency interpretation coherent. Do not simply change a currency label on unchanged economics. |
| FP-03: wrong collateral branch | Every collateral component must include a security classification, including a commodity component. | Check the security/commodity applicability distinction in D04 and the current UK schema. A later valid commodity fixture must also satisfy its own classification and product constraints. |
| FP-04: classification overrestriction | Only the first sub-product illustrated in the classification table is permitted. | Review the relevant parent-child combinations. Prepare two distinct permitted combinations under the applicable taxonomy, plus a prohibited combination as a sensitivity check. Flattened table layout must be resolved before approving those combinations. |
| FP-05: extra condition in a timestamp rule | Adding an agreement or collateral definition to the evidence causes the model to add that field to the clearing timestamp rule without supporting evidence. | Compare extraction from a focused evidence packet with extraction from the same packet plus the supplementary passages. Inspect every added predicate. This tests evidence use, not universal independence between the fields. |
| FP-06: abstention becomes failure | A missing clearing model or unresolved source amendment is automatically treated as proof that the submitted trade is invalid. | Separate missing evidence for a rule's applicability from an independently defined mandatory-data violation. Record the unresolved outcome; do not count it as a successful rejection. |

## How to make valid variation tests meaningful

For each selected rule, prepare a reviewed valid baseline and a second reviewed valid case with a changed supplementary field or coherent field group. Compare the outcome of that specific rule. The entire report can have other validations, so unchanged output from every rule is not the default expectation.

Keep the rule's applicability conditions unchanged when testing invariance. If the variation changes product type, collateral branch, or the contractual situation, test the appropriate change of applicability instead. This is especially relevant to 2.70 and 2.79.

Include genuine violations alongside valid controls so that a validator that passes everything cannot appear successful. Keep reviewer labels separate from model inputs and adjudicate rules independently of the model that proposed them.

Record incorrect rejections divided by reviewed valid cases, and unsupported asserted requirements divided by reviewed asserted requirements, as separate metrics. Record unresolved cases separately. A handful of random fields is useful for finding errors, but cannot establish a zero false-positive rate.

## Current status

Broader field selection, reproducible random sampling, and source passages are prepared. Human-approved trade fixtures, applicability decisions, model outputs, and measured false-positive rates are still pending.
