# Difficult SFTR investigations supported by this corpus

This index identifies **where to investigate**, not the correct outputs of a completed validator. The questions are locally authored; the evidence is in the retrieved documents. Field lists are starting points and may need expansion.

Use this file for selecting an investigation. Keep it outside the model's source inputs during a blind requirement-discovery test.

Every case requires a separate UK applicability assessment. In particular, D07 answers dated after 31 December 2020 are EU clarification material whose UK status has not been established here.

## Source key

- **D02:** [FCA transition statement](../documents/D02_fca_transition_statement.txt).
- **D03:** [FCA 2020/52 amendments](../documents/D03_fca_2020_52_amendments.txt).
- **D04:** [Original RTS 2019/356](../documents/D04_rts_2019_356_original.txt).
- **D05:** [Original ITS 2019/363](../documents/D05_its_2019_363_original.txt).
- **D06:** [ESMA reporting guidelines](../documents/D06_esma_sftr_guidelines.txt).
- **D07:** [ESMA Q&A archive](../documents/D07_esma_sftr_qa_2023.txt).

`L` references below are the preserved source-line markers within those files. They are not editor line numbers. Section references supplement them where available.

## 1. Clearing model changes the timestamp relationship

**Question:** What evidence distinguishes an open-offer clearing event from novation or Delivery by Value, and how should that distinction affect timestamp and identity checks?

**Fields:** 2.5, 2.6, 2.12 initially; expand to 2.2, 2.7, 2.19 and counterparty role.

**Read:** D06 section 5.3.2, L4325–4725; D04 Table 2, L269–320.

**Additional evidence needed in trade data:** clearing model and whether the reporting party is the CCP, clearing member, or client. A single universal timestamp inequality may lose a scenario distinction.

## 2. A reported bilateral trade is subsequently cleared

**Question:** How should a later clearing event be represented across the original and resulting transactions? How does same-day on-venue clearing change the investigation?

**Fields:** 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 2.98; execution and clearing history.

**Read:** D04 Article 2, L68–77; D06 sections 4.3, 4.10, 5.2, and 5.3.2.

**Additional evidence needed:** whether the original transaction was already reported, the venue, event order, and the identities of resulting transactions. Checking one row cannot establish completeness of the reporting sequence.

## 3. Contract existence, failed clearing, and failed settlement

**Question:** Which business facts distinguish a contract that never became effective from an existing contract that subsequently terminates or experiences a temporary settlement failure?

**Fields:** 2.1, 2.3, 2.14, 2.15, 2.98, plus the contractual clearing condition.

**Read:** D06 section 4.9.1, L785–807; D04 action definitions, L765–790; D07 Question 2, L224–278.

**Additional evidence needed:** contract terms, CCP acceptance or rejection, and settlement events. A generic operational status of “failed” does not describe these distinctions.

## 4. Position-component history survives a later correction

**Question:** After a trade becomes a position component and then receives a correction, which historical restrictions still need to be considered? Which identifier should subsequent activity address?

**Fields:** 2.1, 2.98, 2.99, 2.3, and the relationship between trade and position identifiers.

**Read:** D06 section 4.8.3, L658–784, especially L710–727; section 5.2, L3762–4310; D04 level definition, L791–795.

**Additional evidence needed:** accepted submission history and position membership. This investigates the difference between an immediate transition table and restrictions induced by earlier events. The extracted table layout itself requires visual verification.

## 5. Historical modifications versus the current trade state

**Question:** How should backdated modifications, reporting order, and the current outstanding state be considered together? What changes when the intervening days include holidays?

**Fields:** 1.1, 2.1, 2.3, 2.14, 2.15, 2.98.

**Read:** D06 L728–765 and L808–837; D07 Questions 6 and 7, L322–405; D05 Article 5.

**Additional evidence needed:** accepted and rejected submission history, reporting calendar, current state, and the purpose of each historical report. D07 Questions 6 and 7 were published on 28 January 2021; their UK applicability remains unresolved.

## 6. Failed closing settlement around maturity

**Question:** What changes when a closing-leg failure is discovered before or after the available amendment window, or after early termination? Can a net settlement failure be attributed to an individual trade?

**Fields:** 2.1, 2.3, 2.14, 2.15, 2.98; reporting timestamp and outstanding status.

**Read:** D06 section 4.9.5, L890–920; D07 Question 2, L224–278, and Question 7, L353–405.

**Additional evidence needed:** actual settlement, discovery time, both counterparties' reporting histories, and allocation of net fails. Question 2 is marked updated on 25 January 2022.

## 7. Trade collateral and net-exposure collateral coexist

**Question:** How should transaction-specific collateral be distinguished from variation margin across a netting set without counting the same exposure incorrectly?

**Fields:** 2.1, 2.9, 2.73, 2.74, collateral components in 2.75–2.94, and 2.98.

**Read:** D07 Question 3, L279–295; D04 Article 3, L78–110; D06 section 5.4.7, starting around L7804, including Tables 94–98.

**Additional evidence needed:** master agreement, netting-set membership, collateral allocations, and reporting-party perspective. Question 3 was published on 5 November 2020; assess it with D02 and the UK technical package.

## 8. Prepaid collateral must be linked across several trades

**Question:** Which trades should a collateral update apply to when its event date and collateral value date differ?

**Fields:** 1.3, 1.11, 2.9, 2.3, 2.74, 2.13, 2.14.

**Read:** D06 section 5.4.8 and Table 99, L10764–10885; D04 definition of 2.74, L634–638.

**Additional evidence needed:** the set of outstanding loans, their dates, and consistent counterparty/master-agreement identifiers. This is a temporal join problem, not just a comparison between two dates in one row.

## 9. Unknown collateral allocation is different from uncollateralised lending

**Question:** How should an agreed basket, unavailable component information, and genuinely uncollateralised securities lending be distinguished across the initial report and subsequent updates?

**Fields:** 2.72, 2.96, 2.75–2.94, 2.13, 2.3, 2.98.

**Read:** D04 Article 3 and field 2.72; D06 sections 5.4.1–5.4.2, L6080–6535, plus reconciliation discussion near L12365–12400.

**Additional evidence needed:** the agreement to provide collateral, when basket/component information became available, and prior submissions. Absence of detailed components does not explain the business reason for their absence.

## 10. Margin loan drawn, reduced to zero, and drawn again

**Question:** What changes across never-drawn, outstanding, zero-balance, and redrawn states? Where does the general zero-collateral example cease to be sufficient?

**Fields:** 2.4, 2.69, 2.71, 2.75, 2.78, 2.98; relevant collateral values.

**Read:** D05 Article 5(2); D06 L805–807, L864–873, and section 5.4.4 at L6571 onward; D07 Question 5, L311–321.

**Additional evidence needed:** previous exposure, cash debit balance, short market value, and whether the facility was closed. D07 Question 5 was published on 5 November 2020; its technical encoding needs checking against the UK workbook/schema.

## 11. Benchmark movement, agreed re-rating, and a scheduled rate change

**Question:** Which changes represent a reporting event, and which rate fields belong to each business situation?

**Fields:** 2.23, 2.25, 2.32, 2.35, 2.36, 2.59, 2.98.

**Read:** D06 section 5.3.9, L5164–5336; section 4.9.2, L808–837; D07 Question 10, L570–597.

**Additional evidence needed:** agreed terms, effective date, benchmark identity, and whether the change was scheduled at inception. Question 10 is marked updated on 20 May 2021; avoid treating its historical code guidance as automatically current in the UK.

## 12. Intraday, overnight, and final-day reporting

**Question:** How do trade-state inclusion and the obligation to submit valuation/collateral updates differ around the last day of a transaction?

**Fields:** 2.3, 2.12, 2.14, 2.15, 2.98, and the relevant valuation/collateral fields.

**Read:** D05 Article 5(3)–(4); D06 sections 4.8–4.9; D07 Questions 13 and 14, L637–662.

**Additional evidence needed:** product type, event dates, reporting date, and outstanding status. The two Q&A answers were updated on 7 July 2022. This is also a version/applicability investigation, not permission to combine every historical statement into one UK rule.

## 13. CCP margin, transaction collateral, and a shared portfolio code

**Question:** How should portfolio-level margin be linked to cleared SFTs while keeping it distinct from transaction collateral and from derivative positions?

**Fields:** 2.5, 2.7, 2.97; 3.4, 3.6, 3.7, margin amounts/currencies, and 3.20.

**Read:** D04 field 2.97, L758–763, and Table 3, L797–919; D05 Article 5(5); D06 section 5.5, L10886–11037.

**Additional evidence needed:** portfolio membership, clearing relationships, posting/receiving perspective, and any shared portfolio identifiers. A numerical comparison of total margin with one trade's collateral is not enough to establish a valid rule.

## 14. Reuse entitlement versus actual or estimated reuse

**Question:** How should contractual reuse eligibility be separated from reuse activity and the entity-level reporting lifecycle?

**Fields:** 2.20, 2.95; Table 4 reporting identity, instrument, reuse values, event date, and action type.

**Read:** D04 Article 4 and Table 4; D06 section 5.4.5.3, L6844–6860, and section 5.6, L11038–12039; D05 Article 5(6).

**Additional evidence needed:** collateral agreement, inventory, actual reuse or estimation inputs, and prior aggregate reports. The transaction-level and entity-level records have different units of observation.

## 15. An erroneous cancellation and duplicate reporting to two repositories

**Question:** Which identifiers and counterparties are affected by an erroneous cancellation, and how does a duplicate submission to a second repository change the analysis? Does the same reasoning apply to reuse reports?

**Fields:** 2.1, 2.98, reporting counterparties, repository identity; separate Table 4 identities/action history.

**Read:** D06 section 4.8.3, L766–784; D04 action definitions and Table 4.

**Additional evidence needed:** both repositories' accepted reports, both counterparties' submissions, and the report family. A state machine keyed only by UTI would omit relevant context.

## 16. UK counterparty classification and branch scope

**Question:** How should reporting scope and field classification be investigated for funds, branches, and different counterparty types when the corpus includes both original EU definitions and UK amendments?

**Fields:** 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10.

**Read:** D02 L25–53 and L72–80; D03 Annexes A and B; D04 Table 1, L139–211; D05 Annex I, Table 1; D06 sections 4.4–4.7 and 5.1.

**Additional evidence needed:** legal entity/fund type, establishment, branch through which the trade was concluded, and reporting responsibility. D03's lost redline styling prevents confidently resolving amendments from this text snapshot alone.

## What is still needed before these become scored tests

These are 16 investigation targets, not 16 approved validation rules. After selecting one, the next work is to establish the applicable UK evidence, resolve extraction ambiguities, and prepare independently reviewed expected outcomes for concrete records and histories. Current FCA workbook/schema contents are still missing from this collection.

Do not score a model as wrong merely because it identifies missing evidence or an unresolved jurisdiction/version issue. Those are legitimate outcomes for the material collected here.
