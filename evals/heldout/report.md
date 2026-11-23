# Evaluation report

**Samples:** 28 | **Expected items:** 545 | **Model:** claude-sonnet-5-5 | **Run date:** 2026-11-23 | **Report date:** 2026-11-23

## v2 scores (spec R15.1)

**Set:** heldout | **Calls:** 28 | **Runs per call:** 5 | **Prompt version:** 2.1 | **Calls written by:** Claude (AI) drafted; approved by Aswin Guruswamy on 2026-11-23

| Metric | Result |
|---|---|
| Recall | 95% |
| Precision | 99% |
| Invented owners (release gate: 0) | 0 |
| Invented dates (release gate: 0) | 0 |
| Wrong owners | 0 |
| Wrong dates | 0 |
| Owner state correct | 523 of 524 |
| Items found in all 5 runs | 94% |
| Owner the key forbids (release gate: 0) | 0 |
| Extra items with an owner or a date (check by hand) | 0 |


## Scores by item type

| Type | Expected | Found by tool | Recall | Precision |
|---|---|---|---|---|
| Risk | 50 | 50 | 100% | 100% |
| Assumption | 30 | 34 | 100% | 88% |
| Issue | 110 | 101 | 95% | 100% |
| Dependency | 60 | 61 | 92% | 95% |
| Action | 250 | 235 | 94% | 100% |
| Decision | 45 | 45 | 100% | 100% |
| **All** | **545** | **526** | **95%** | **99%** |

## Charter targets

| Metric | Target | Result | Met |
|---|---|---|---|
| Recall on risks, issues, dependencies, actions | 85% or more | 94% | ✅ |
| Precision on all item types | 80% or more | 99% | ✅ |
| Owners or dates that the tool invents (v2 definitions) | 0 | 0 | ✅ |

## Owners and dates (on matched items)

| Check | Result |
|---|---|
| Correct owner | 205 of 205 (100%) |
| Correct due date | 138 of 149 (93%) |
| Owner given where the notes name nobody | 0 |
| Owner not in the notes at all (v1 check) | 0 |
| Date not written as YYYY-MM-DD in the notes (v1 check; v2 converts date words) | 138 |

## Cost and time

All 140 call runs: $1.7776 in total, 540.0 s in total (average $0.0127 and 3.9 s for each call run).

## Manual baseline (story S2-03, KAN-17)

| Sample | Manual RAID log | Tool run |
|---|---|---|
| s02_crm_migration.txt | 8 min | - |
| s05_erp_steering.docx | 6 min | - |
| s07_cloud_migration.vtt | 6 min | - |

Manual times were measured on 2026-10-20 (s02: 17:32-17:40, s05: 17:46-17:52, s07: 17:57-18:03). These samples are short (about 140-160 words). Notes from a 1-hour call are much longer, so the manual time for a real call is higher. The charter's assumption of 20-40 minutes for a full call is not yet measured.

## Details by sample

**h01_warehouse_scanners.txt (run 1)** — expected 5, found 5, matched 5

**h02_website_redesign.txt (run 1)** — expected 5, found 5, matched 5

**h03_mobile_release.txt (run 1)** — expected 5, found 5, matched 5

**h04_data_warehouse.txt (run 1)** — expected 5, found 5, matched 5

**h05_customer_conference.txt (run 1)** — expected 4, found 4, matched 4

**h06_hr_system.txt (run 1)** — expected 4, found 4, matched 4

**h07_payroll_migration.txt (run 1)** — expected 3, found 3, matched 3

**h08_supplier_audit.txt (run 1)** — expected 5, found 4, matched 4
- Missed: Action: Get the audit folder ready

**h09_ecommerce_launch.txt (run 1)** — expected 6, found 6, matched 6

**h10_billing_upgrade.txt (run 1)** — expected 4, found 4, matched 4

**h11_marketing_campaign.txt (run 1)** — expected 4, found 4, matched 4

**h12_clinic_scheduling.txt (run 1)** — expected 4, found 4, matched 4

**h13_bank_reporting.txt (run 1)** — expected 3, found 3, matched 3

**h14_factory_maintenance.txt (run 1)** — expected 3, found 3, matched 3
- Type mix-up: expected Dependency, tool said Assumption: New bearings arrive on 12 December

**h15_school_portal.txt (run 1)** — expected 4, found 3, matched 3
- Missed: Action: Attendance export, planned for the next sprint

**h16_charity_gala.txt (run 1)** — expected 3, found 3, matched 3

**h17_it_migration.txt (run 1)** — expected 4, found 4, matched 4

**h18_retail_pricing.txt (run 1)** — expected 2, found 2, matched 2

**h19_data_platform.txt (run 1)** — expected 3, found 3, matched 3

**h20_mobile_banking.txt (run 1)** — expected 4, found 2, matched 2
- Missed: Action: Decide on card freeze after the security review
- Missed: Issue: Security review not done

**h21_hr_policy.txt (run 1)** — expected 2, found 2, matched 2

**h22_load_testing.txt (run 1)** — expected 3, found 3, matched 3

**h23_vendor_choice.txt (run 1)** — expected 3, found 3, matched 3

**h24_weekly_standup.txt (run 1)** — expected 0, found 0, matched 0

**h25_warehouse_move.txt (run 1)** — expected 4, found 4, matched 4

**h26_crm_cleanup.txt (run 1)** — expected 4, found 4, matched 4

**h27_security_patch.txt (run 1)** — expected 3, found 2, matched 2
- Missed: Issue: October security patch not on the web servers

**h28_erp_long_call.txt (run 1)** — expected 10, found 10, matched 10

**h01_warehouse_scanners.txt (run 2)** — expected 5, found 5, matched 5

**h02_website_redesign.txt (run 2)** — expected 5, found 5, matched 5

**h03_mobile_release.txt (run 2)** — expected 5, found 5, matched 5

**h04_data_warehouse.txt (run 2)** — expected 5, found 5, matched 5

**h05_customer_conference.txt (run 2)** — expected 4, found 4, matched 4

**h06_hr_system.txt (run 2)** — expected 4, found 4, matched 4

**h07_payroll_migration.txt (run 2)** — expected 3, found 3, matched 3

**h08_supplier_audit.txt (run 2)** — expected 5, found 4, matched 4
- Missed: Action: Get the audit folder ready

**h09_ecommerce_launch.txt (run 2)** — expected 6, found 6, matched 6

**h10_billing_upgrade.txt (run 2)** — expected 4, found 5, matched 4
- Extra: Dependency: The retest of the invoice template depends on the fix being installed first.

**h11_marketing_campaign.txt (run 2)** — expected 4, found 4, matched 4

**h12_clinic_scheduling.txt (run 2)** — expected 4, found 4, matched 4

**h13_bank_reporting.txt (run 2)** — expected 3, found 3, matched 3

**h14_factory_maintenance.txt (run 2)** — expected 3, found 3, matched 3
- Type mix-up: expected Dependency, tool said Assumption: New bearings arrive on 12 December

**h15_school_portal.txt (run 2)** — expected 4, found 3, matched 3
- Missed: Action: Attendance export, planned for the next sprint

**h16_charity_gala.txt (run 2)** — expected 3, found 3, matched 3

**h17_it_migration.txt (run 2)** — expected 4, found 4, matched 4

**h18_retail_pricing.txt (run 2)** — expected 2, found 2, matched 2

**h19_data_platform.txt (run 2)** — expected 3, found 3, matched 3

**h20_mobile_banking.txt (run 2)** — expected 4, found 3, matched 3
- Missed: Action: Decide on card freeze after the security review

**h21_hr_policy.txt (run 2)** — expected 2, found 2, matched 2

**h22_load_testing.txt (run 2)** — expected 3, found 3, matched 3

**h23_vendor_choice.txt (run 2)** — expected 3, found 3, matched 3

**h24_weekly_standup.txt (run 2)** — expected 0, found 0, matched 0

**h25_warehouse_move.txt (run 2)** — expected 4, found 4, matched 4

**h26_crm_cleanup.txt (run 2)** — expected 4, found 4, matched 4

**h27_security_patch.txt (run 2)** — expected 3, found 2, matched 2
- Missed: Issue: October security patch not on the web servers

**h28_erp_long_call.txt (run 2)** — expected 10, found 10, matched 10

**h01_warehouse_scanners.txt (run 3)** — expected 5, found 5, matched 5

**h02_website_redesign.txt (run 3)** — expected 5, found 5, matched 5

**h03_mobile_release.txt (run 3)** — expected 5, found 5, matched 5

**h04_data_warehouse.txt (run 3)** — expected 5, found 5, matched 5

**h05_customer_conference.txt (run 3)** — expected 4, found 4, matched 4

**h06_hr_system.txt (run 3)** — expected 4, found 4, matched 4

**h07_payroll_migration.txt (run 3)** — expected 3, found 3, matched 3

**h08_supplier_audit.txt (run 3)** — expected 5, found 4, matched 4
- Missed: Action: Get the audit folder ready

**h09_ecommerce_launch.txt (run 3)** — expected 6, found 6, matched 6

**h10_billing_upgrade.txt (run 3)** — expected 4, found 5, matched 4
- Extra: Dependency: The QA retest of the invoice template depends on the fix being installed first.

**h11_marketing_campaign.txt (run 3)** — expected 4, found 4, matched 4

**h12_clinic_scheduling.txt (run 3)** — expected 4, found 4, matched 4

**h13_bank_reporting.txt (run 3)** — expected 3, found 3, matched 3

**h14_factory_maintenance.txt (run 3)** — expected 3, found 3, matched 3
- Type mix-up: expected Dependency, tool said Assumption: New bearings arrive on 12 December

**h15_school_portal.txt (run 3)** — expected 4, found 3, matched 3
- Missed: Action: Attendance export, planned for the next sprint

**h16_charity_gala.txt (run 3)** — expected 3, found 3, matched 3

**h17_it_migration.txt (run 3)** — expected 4, found 4, matched 4

**h18_retail_pricing.txt (run 3)** — expected 2, found 2, matched 2

**h19_data_platform.txt (run 3)** — expected 3, found 3, matched 3

**h20_mobile_banking.txt (run 3)** — expected 4, found 3, matched 3
- Missed: Action: Decide on card freeze after the security review

**h21_hr_policy.txt (run 3)** — expected 2, found 2, matched 2

**h22_load_testing.txt (run 3)** — expected 3, found 3, matched 3

**h23_vendor_choice.txt (run 3)** — expected 3, found 3, matched 3

**h24_weekly_standup.txt (run 3)** — expected 0, found 0, matched 0

**h25_warehouse_move.txt (run 3)** — expected 4, found 4, matched 4

**h26_crm_cleanup.txt (run 3)** — expected 4, found 4, matched 4

**h27_security_patch.txt (run 3)** — expected 3, found 3, matched 3

**h28_erp_long_call.txt (run 3)** — expected 10, found 10, matched 10

**h01_warehouse_scanners.txt (run 4)** — expected 5, found 5, matched 5

**h02_website_redesign.txt (run 4)** — expected 5, found 5, matched 5

**h03_mobile_release.txt (run 4)** — expected 5, found 5, matched 5

**h04_data_warehouse.txt (run 4)** — expected 5, found 5, matched 5

**h05_customer_conference.txt (run 4)** — expected 4, found 4, matched 4

**h06_hr_system.txt (run 4)** — expected 4, found 4, matched 4

**h07_payroll_migration.txt (run 4)** — expected 3, found 3, matched 3

**h08_supplier_audit.txt (run 4)** — expected 5, found 4, matched 4
- Missed: Action: Get the audit folder ready

**h09_ecommerce_launch.txt (run 4)** — expected 6, found 6, matched 6

**h10_billing_upgrade.txt (run 4)** — expected 4, found 4, matched 4

**h11_marketing_campaign.txt (run 4)** — expected 4, found 4, matched 4

**h12_clinic_scheduling.txt (run 4)** — expected 4, found 4, matched 4

**h13_bank_reporting.txt (run 4)** — expected 3, found 3, matched 3

**h14_factory_maintenance.txt (run 4)** — expected 3, found 2, matched 2
- Missed: Dependency: New bearings arrive on 12 December

**h15_school_portal.txt (run 4)** — expected 4, found 3, matched 3
- Missed: Action: Attendance export, planned for the next sprint

**h16_charity_gala.txt (run 4)** — expected 3, found 3, matched 3

**h17_it_migration.txt (run 4)** — expected 4, found 4, matched 4

**h18_retail_pricing.txt (run 4)** — expected 2, found 2, matched 2

**h19_data_platform.txt (run 4)** — expected 3, found 3, matched 3

**h20_mobile_banking.txt (run 4)** — expected 4, found 3, matched 3
- Missed: Action: Decide on card freeze after the security review

**h21_hr_policy.txt (run 4)** — expected 2, found 2, matched 2

**h22_load_testing.txt (run 4)** — expected 3, found 3, matched 3

**h23_vendor_choice.txt (run 4)** — expected 3, found 3, matched 3

**h24_weekly_standup.txt (run 4)** — expected 0, found 0, matched 0

**h25_warehouse_move.txt (run 4)** — expected 4, found 4, matched 4

**h26_crm_cleanup.txt (run 4)** — expected 4, found 4, matched 4

**h27_security_patch.txt (run 4)** — expected 3, found 2, matched 2
- Missed: Issue: October security patch not on the web servers

**h28_erp_long_call.txt (run 4)** — expected 10, found 10, matched 10

**h01_warehouse_scanners.txt (run 5)** — expected 5, found 5, matched 5

**h02_website_redesign.txt (run 5)** — expected 5, found 5, matched 5

**h03_mobile_release.txt (run 5)** — expected 5, found 5, matched 5

**h04_data_warehouse.txt (run 5)** — expected 5, found 5, matched 5

**h05_customer_conference.txt (run 5)** — expected 4, found 4, matched 4

**h06_hr_system.txt (run 5)** — expected 4, found 4, matched 4

**h07_payroll_migration.txt (run 5)** — expected 3, found 3, matched 3

**h08_supplier_audit.txt (run 5)** — expected 5, found 4, matched 4
- Missed: Action: Get the audit folder ready

**h09_ecommerce_launch.txt (run 5)** — expected 6, found 6, matched 6

**h10_billing_upgrade.txt (run 5)** — expected 4, found 4, matched 4

**h11_marketing_campaign.txt (run 5)** — expected 4, found 4, matched 4

**h12_clinic_scheduling.txt (run 5)** — expected 4, found 4, matched 4

**h13_bank_reporting.txt (run 5)** — expected 3, found 3, matched 3

**h14_factory_maintenance.txt (run 5)** — expected 3, found 3, matched 3
- Type mix-up: expected Dependency, tool said Assumption: New bearings arrive on 12 December

**h15_school_portal.txt (run 5)** — expected 4, found 3, matched 3
- Missed: Action: Attendance export, planned for the next sprint

**h16_charity_gala.txt (run 5)** — expected 3, found 3, matched 3

**h17_it_migration.txt (run 5)** — expected 4, found 4, matched 4

**h18_retail_pricing.txt (run 5)** — expected 2, found 2, matched 2

**h19_data_platform.txt (run 5)** — expected 3, found 3, matched 3

**h20_mobile_banking.txt (run 5)** — expected 4, found 3, matched 3
- Missed: Issue: Security review not done
- Type mix-up: expected Action, tool said Dependency: Decide on card freeze after the security review

**h21_hr_policy.txt (run 5)** — expected 2, found 2, matched 2

**h22_load_testing.txt (run 5)** — expected 3, found 3, matched 3

**h23_vendor_choice.txt (run 5)** — expected 3, found 3, matched 3

**h24_weekly_standup.txt (run 5)** — expected 0, found 0, matched 0

**h25_warehouse_move.txt (run 5)** — expected 4, found 4, matched 4

**h26_crm_cleanup.txt (run 5)** — expected 4, found 4, matched 4

**h27_security_patch.txt (run 5)** — expected 3, found 2, matched 2
- Missed: Issue: October security patch not on the web servers

**h28_erp_long_call.txt (run 5)** — expected 10, found 10, matched 10

## How to read this report

- **Recall:** of the items that are in the notes, the share that the tool found with an accepted type.
- **Precision:** of the items that the tool reported, the share that are correct.
- **Matching:** a tool item matches an expected item when its source quote shares most of its words with the expected evidence (see `raid/evaluate.py`).

## Known limits

- 28 samples and 545 expected items: the scores show a direction, not a statistical proof.
- The samples and the correct answers were written with AI help (Claude), and the tool also uses Claude. This can make the samples easier for the tool than real notes.
- The correct answers were committed before the tool ran on the samples (see the Git history).
