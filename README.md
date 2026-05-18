# Document Summary

**National Technical University of Athens (NTUA) — Databases Semester Project 2025-2026**

## The Task

Design and implement a hospital information system for "Ygeiopolis General Hospital" using MariaDB or PostgreSQL (no ORMs, no ENUMs/arrays/JSON/XML).

---

## Domain Description

**Staff** (shared attributes: AMKA, name, surname, age, email, phone, hire date, type):

- **Doctors** — medical license number, specialty, rank (Resident → Registrar B → Registrar A → Director). Each doctor may have a supervisor (also a doctor). Residents _must_ have a supervisor; Directors _cannot_. No circular supervision chains. Doctors belong to one or more departments.
- **Nurses** — rank (Assistant, Nurse, Head Nurse). Belong to exactly one department.
- **Administrative staff** — role (e.g. Secretary, Accountant), office, one department.

**Departments** (e.g. Cardiology, Surgery, ICU, ER) — name, description, bed count, floor/building, one director (a doctor). Each department has **beds** with a unique number, type (ICU, single, multi-bed), and status (available, occupied, under maintenance).

**Patients** — AMKA, name, surname, father's name, age, gender, weight, height, address, phone, email, occupation, nationality, emergency contacts, insurance provider (EFKA, private, uninsured). Patients can have multiple hospitalizations.

**Shifts (On-Call)** — 3 daily 8-hour shifts per department: Morning (07–15), Afternoon (15–23), Night (23–07). Each shift must have: ≥3 doctors, ≥6 nurses, ≥2 admin staff. If a Resident is on shift, at least one Registrar A or Director must also be present. Limits per month: doctors ≤15, nurses ≤20, admin ≤25. Minimum 8h rest between consecutive shifts per person. No more than 3 consecutive night shifts per person. These constraints are enforced by the system.

**ER Triage** — nurses record symptoms and assign urgency level 1–5. Patients served by urgency, then FIFO within same level. Patient either gets instructions and leaves, or gets admitted.

**Hospitalizations** — patient, bed, department, admission/discharge date, admission/discharge diagnosis (ICD-10 code + description), total cost. Costing uses the KEN (DRG) system: each hospitalization maps to a KEN code with a base cost and a Mean Length of Stay (MLOS). If actual stay exceeds MLOS, a daily surcharge applies.

**Lab Tests** — linked to a hospitalization; code, type, date, result (text and/or numeric with unit), cost, ordering doctor.

**Medical Procedures/Surgeries** — code, name, category (surgical/diagnostic/therapeutic), duration, cost, required room (OR or procedure room). Has one primary surgeon and optional assistants (doctors or nurses). No two procedures can occur simultaneously in the same room; no doctor can participate in two simultaneous procedures.

**Medication** — always prescribed by a doctor (doctor, patient, drug, start date unique together). Includes dosage, frequency, start/end date. Must follow EMA Article 57 database. Patients can have recorded allergies to active substances. Prescribing a drug whose active substance a patient is allergic to is forbidden.

**Patient Reviews** — only after completed hospitalization. Likert scale on: nursing care quality, cleanliness, food, overall experience. Doctors rated on: medical care quality (by patients they prescribed to during that hospitalization).

**Images** — all entities should support associated images with a text description (for a future website).

---

## Required Queries (15 total, equal weight)

|#|Description|
|---|---|
|Q1|Hospital revenue per department per year, broken down by KEN code (base cost vs. surcharge) and by insurance provider|
|Q2|All doctors of a given specialty, whether they had a shift this year, and how many surgeries they performed as primary surgeon|
|Q3|Patients hospitalized more than 3 times in the same department, with total cost|
|Q4|For a given doctor: avg patient rating (medical care) and avg overall hospitalization rating _(+ EXPLAIN analysis)_|
|Q5|Young doctors (age < 35) who performed the most surgical procedures as primary surgeon|
|Q6|For a given patient: full hospitalization history, ICD-10 diagnoses, cost per stay, avg rating _(+ EXPLAIN analysis)_|
|Q7|Per active substance: number of patients with that allergy and number of drugs containing it, sorted by allergy count|
|Q8|Staff (all types) with no scheduled shift on a given date and department|
|Q9|Patients hospitalized the same number of days in a given year, with total duration > 15 days|
|Q10|Top-3 pairs of active substances co-prescribed to the same patient in the same hospitalization|
|Q11|Doctors who performed at least 5 fewer procedures than the top doctor this year|
|Q12|Required staffing per department per shift for a given week, broken down by sub-category (doctors by specialty, nurses by rank, admin by role)|
|Q13|Full supervision hierarchy for each doctor, from direct supervisor up to Director, with level indicator _(requires recursive CTE)_|
|Q14|ICD-10 diagnosis categories with the same admission count in two consecutive years (≥5 cases/year)|
|Q15|Triage distribution by urgency level: avg wait time, % leading to hospitalization, referral breakdown by department|

---

## Deliverables (due 17 May 2026)

A `.zip` with:

- `README.md` — documentation + assumptions
- `diagrams/er.pdf` — ER diagram
- `diagrams/relational.pdf` — relational schema
- `sql/install.sql` — DDL
- `sql/load.sql` — data loading script
- `sql/Q01.sql` … `Q15.sql` + corresponding `_out.txt` files
- `docs/report.pdf` — report with screenshots for Q4 and Q6
- (optional) `code/` — web UI for up to 10 bonus points

**Demo: 18–22 May 2026. Attendance mandatory.**

---

# Roadmap

Here's how I'd approach this project in phases, assuming you're working solo or in a small team.

---

## Phase 1 — ER Design (Days 1–3)

Start on paper or a tool like draw.io / Lucidchart.

Key decisions to nail:

- **Staff inheritance** — use a single `staff` table with type discriminator + separate `doctors`, `nurses`, `admin` tables (class-table inheritance). Avoids NULLs, cleanest for SQL queries.
- **Supervisor self-referencing** — `doctor.supervisor_id → doctor.amka` (nullable FK). The no-circular-chain constraint is a CHECK or trigger.
- **Doctor ↔ Department** — many-to-many join table `doctor_department`.
- **Shift coverage** — a `shift` table (department, date, shift_type) and a `shift_assignment` table linking staff members to shifts. Constraints enforced via triggers or application logic.
- **KEN costing** — a `ken` reference table with `base_cost` and `mean_los`. Actual cost computed at query time or stored with a trigger.
- **EMA drugs + active substances** — two tables: `drugs` and `active_substances`, linked many-to-many via `drug_active_substance`. Patient allergies → `patient_allergy(patient_amka, substance_id)`.
- **Images** — a generic `entity_image(entity_type, entity_id, url, description)` table or per-entity image tables.

---

## Phase 2 — Relational Schema + DDL (Days 4–6)

Translate ER → relational. Write `install.sql` with:

- All tables with proper data types
- Primary keys, foreign keys
- `NOT NULL`, `UNIQUE`, `CHECK` constraints (e.g. `urgency_level BETWEEN 1 AND 5`)
- Triggers for complex constraints:
    - No circular supervision
    - Shift staffing minimums (≥3 doctors, ≥6 nurses, ≥2 admin)
    - Resident on shift → must have Registrar A or Director
    - Monthly shift limits per staff category
    - 8h rest between shifts
    - Max 3 consecutive night shifts
    - Drug allergy check on prescription insert
    - No overlapping procedures in same room or for same doctor

Write indexes in `install.sql` too (see Phase 4).

---

## Phase 3 — Reference Data Loading (Days 7–9)

Load official datasets into the DB:

- **ICD-10 codes** — from Ministry of Health XLS
- **KEN codes** — from Ministry of Health
- **Medical procedure codes** — categories A–E from Ministry of Health
- **EMA Article 57 drugs** — large XLSX, `|`-delimited active substances; preprocess with Python/Excel before `LOAD DATA INFILE`

This is tedious but required — fabricated codes are not accepted.

---

## Phase 4 — Synthetic Data Generation (Days 10–13)

Write `load.sql` or a Python script that generates and inserts:

- 15 departments, beds per department
- 80 doctors (with supervision hierarchy, specialties, ranks)
- ~100 nurses, ~50 admin staff
- 200 patients (with allergies, emergency contacts)
- Shifts covering multiple weeks/months
- 500 hospitalizations (with KEN codes, ICD-10 diagnoses, dates)
- 200 lab tests, 150 medical procedures (with staff assignments, rooms, no overlaps)
- 300 prescriptions (respecting allergy constraints)
- Reviews for completed hospitalizations
- Triage records (urgency levels, arrival times)

Make sure data satisfies all 15 query conditions — e.g. some patients hospitalized 4+ times in same department (Q3), some doctors under 35 with surgeries (Q5), consecutive-year ICD-10 data (Q14).

---

## Phase 5 — Write the 15 Queries (Days 14–20)

Tackle them roughly in order of complexity:

**Easier first:** Q2, Q3, Q5, Q8, Q11 — straightforward aggregations and filters.

Q2: 
SELECT d.amka,
st.first_name,
st.last_name,
CASE WHEN COUNT(DISTINCT sh.id) > 0 THEN 'Yes' ELSE 'No' END AS had_oncall_this_year,
COUNT(DISTINCT mp.id) AS lead_procedures_this_year
FROM doctor d
JOIN staff st ON st.amka = d.amka
LEFT JOIN medical_procedure mp ON mp.primary_surgeon_amka = d.amka
LEFT JOIN shift_assignment sa ON sa.staff_amka = d.amka
LEFT JOIN shift sh ON sh.id = sa.shift_id AND sh.shift_type = 'Night' AND YEAR(sh.shift_date) = YEAR(CURDATE())
WHERE d.specialty = 'Surgery'
GROUP BY d.amka, st.first_name, st.last_name;


Q3: 


**Medium:** Q1 (multi-level grouping with CASE for cost breakdown), Q7, Q9, Q10 (self-join or window functions for pairs), Q12, Q15.

**Harder:** Q13 (recursive CTE for supervision hierarchy), Q14 (self-join on year-over-year counts), Q4/Q6 (multi-join aggregations + EXPLAIN analysis).

For **Q4 and Q6**, after writing the query:

1. Run `EXPLAIN ANALYZE`
2. Add appropriate index, or use `FORCE INDEX`
3. Compare plans and execution times
4. Write 3–5 sentence analysis

---

## Phase 6 — Indexes (alongside Phase 5)

Add indexes where queries need them. Justify each one. Typical candidates:

- `hospitalization(patient_id)`, `hospitalization(department_id)`, `hospitalization(admission_date)`
- `shift_assignment(staff_id, shift_date)`
- `prescription(patient_amka, drug_id)`
- `patient_allergy(substance_id)`
- `triage(urgency_level, arrival_time)`
- `doctor(specialty)`, `doctor(rank)`

---

## Phase 7 — Report + Packaging (Days 21–23)

- Write `README.md` with your assumptions table
- Export ER and relational diagrams as PDFs
- Capture `Q01_out.txt` … `Q15_out.txt`
- Write `docs/report.pdf` with screenshots for Q4 and Q6 (query, EXPLAIN output, comparison, analysis)
- Package everything into the required zip structure

---

## Optional: Web UI (bonus 10 pts)

A simple Flask/Node.js app with forms for common operations and a page to run/display each query result is enough to qualify. Not worth it if it eats too much time.

## Indexes — Justifications

Summary of indexes created in `lamp/init/mysql-sakila-schema.sql` and rationale for keeping or removing them:

- `idx_drug_name`: Speeds lookups, ORDER/BY and pattern searches on `drug.product_name`.
- `idx_drug_country`: Speeds filters and GROUPs by `product_authorisation_country`.
- `idx_das_substance`: Speeds joins from `drug_active_substance` to `active_substance`.
- `idx_patient_name`: Speeds lookup and sorting by `patient.last_name, patient.first_name`.
- `idx_allergy_substance`: Speeds queries joining `patient_allergy` by `substance_id`.
- `idx_staff_name`: Speeds lookups/sorts by staff name.
- `idx_doctor_specialty`: Speeds finding doctors by specialty.
- `idx_doctor_supervisor`: Speeds hierarchical queries and joins to a supervisor.
- `idx_nurse_dept`: Speeds lookups of nurses by department.
- `idx_admin_dept`: Speeds admin_staff → department lookups.
- `idx_bed_dept`: Speeds joins/filters for beds per department.
- `idx_bed_status`: Although low-cardinality, `status` is often queried (e.g., `Available`) so it's useful.
- `idx_shift_date`: Supports date-range queries and scheduling views.
- `idx_shift_dept`: Supports queries for shifts per department.
- `idx_sa_staff`: Speeds finding assignments for a given staff member.
- `idx_sa_shift`: Speeds finding staff assigned to a given shift.
- `idx_triage_patient`: Speeds lookup of triage records for a patient.
- `idx_triage_arrival`: Supports ordering and range queries on arrival times.
- `idx_hosp_patient`: Frequent join/filter: hospitalizations per patient.
- `idx_hosp_dept`: Hospitalizations per department queries.
- `idx_hosp_admission`: Supports admission-date range queries and reporting.
- `idx_hosp_discharge`: Supports discharge-date queries and reporting.
- `idx_hosp_icd`: Queries by ICD-10 admission code for reporting/epidemiology.
- `idx_hosp_ken`: Queries/grouping by KEN (DRG) code for costing/stats.
- `idx_lt_hosp`: Lab tests → hospitalization joins.
- `idx_lt_doctor`: Lab tests ordered by doctor.
- `idx_lt_date`: Test-date range queries and reporting.
- `idx_proc_hosp`: Procedures per hospitalization.
- `idx_proc_surgeon`: Find procedures by surgeon.
- `idx_proc_room`: Find procedures in a room for scheduling/conflict checks.
- `idx_proc_start`: Range/order queries on procedure start times (used by scheduling/triggers).
- `idx_presc_hosp`: Prescriptions linked to a hospitalization.
- `idx_presc_patient`: Prescriptions per patient.
- `idx_presc_doctor`: Prescriptions per doctor (audit/reporting).
- `idx_presc_drug`: Find prescriptions by drug for pharmacovigilance/counts.
- `idx_rev_hosp_hosp`: Reviews per hospitalization.
- `idx_rev_hosp_patient`: Patient review lookups.
- `idx_rev_doctor_doctor`: Reviews per doctor for rating reports.
- `idx_rev_doctor_hosp`: Join from doctor-review to hospitalization.
- `idx_image_entity`: Composite index `(entity_type, entity_id)` to quickly find images for an entity.

# Q6 Analysis
## a) Analyze output 
```json 
{
  "query_optimization": {
    "r_total_time_ms": 0.216812163
  },
  "query_block": {
    "select_id": 1,
    "cost": 0.033108,
    "r_loops": 1,
    "r_total_time_ms": 0.125738637,
    "nested_loop": [
      {
        "table": {
          "table_name": "h",
          "access_type": "ref",
          "possible_keys": [
            "idx_hosp_patient",
            "idx_hosp_dept",
            "idx_hosp_icd",
            "idx_hosp_ken"
          ],
          "key": "idx_hosp_patient",
          "key_length": "44",
          "used_key_parts": ["patient_amka"],
          "ref": ["const"],
          "loops": 1,
          "r_loops": 1,
          "rows": 3,
          "r_index_rows": 3,
          "r_rows": 3,
          "cost": 0.00708384,
          "r_table_time_ms": 0.02582617,
          "r_other_time_ms": 0.009721439,
          "r_engine_stats": {
            "pages_accessed": 8
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "index_condition": "h.patient_amka = '00545228015'",
          "r_icp_filtered": 100,
          "attached_condition": "h.patient_amka <=> '00545228015'",
          "r_filtered": 100
        }
      },
      {
        "table": {
          "table_name": "d",
          "access_type": "eq_ref",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "4",
          "used_key_parts": ["id"],
          "ref": ["ygeiopolis.h.department_id"],
          "loops": 3,
          "r_loops": 3,
          "rows": 1,
          "r_rows": 1,
          "cost": 0.00350252,
          "r_table_time_ms": 0.006723385,
          "r_other_time_ms": 0.003170717,
          "r_engine_stats": {
            "pages_accessed": 3
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100
        }
      },
      {
        "table": {
          "table_name": "kc",
          "access_type": "eq_ref",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "42",
          "used_key_parts": ["code"],
          "ref": ["ygeiopolis.h.ken_code"],
          "loops": 3,
          "r_loops": 3,
          "rows": 1,
          "r_rows": 1,
          "cost": 0.00514092,
          "r_table_time_ms": 0.013152022,
          "r_other_time_ms": 0.001798135,
          "r_engine_stats": {
            "pages_accessed": 7
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100
        }
      },
      {
        "table": {
          "table_name": "icd_adm",
          "access_type": "eq_ref",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "42",
          "used_key_parts": ["code"],
          "ref": ["ygeiopolis.h.admission_icd10"],
          "loops": 3,
          "r_loops": 3,
          "rows": 1,
          "r_rows": 1,
          "cost": 0.00514092,
          "r_table_time_ms": 0.010701606,
          "r_other_time_ms": 0.002364957,
          "r_engine_stats": {
            "pages_accessed": 6
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100
        }
      },
      {
        "table": {
          "table_name": "icd_dis",
          "access_type": "eq_ref",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "42",
          "used_key_parts": ["code"],
          "ref": ["ygeiopolis.h.discharge_icd10"],
          "loops": 3,
          "r_loops": 3,
          "rows": 1,
          "r_rows": 1,
          "cost": 0.00514092,
          "r_table_time_ms": 0.009051717,
          "r_other_time_ms": 0.003128859,
          "r_engine_stats": {
            "pages_accessed": 6
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "attached_condition": "trigcond(trigcond(h.discharge_icd10 is not null))",
          "r_filtered": 100
        }
      },
      {
        "table": {
          "table_name": "prh",
          "access_type": "ref",
          "possible_keys": ["uq_rev_hosp", "idx_rev_hosp_hosp"],
          "key": "uq_rev_hosp",
          "key_length": "4",
          "used_key_parts": ["hospitalization_id"],
          "ref": ["ygeiopolis.h.id"],
          "loops": 3,
          "r_loops": 3,
          "rows": 1,
          "r_rows": 0.666666667,
          "cost": 0.00709888,
          "r_table_time_ms": 0.011043443,
          "r_other_time_ms": 0.023775145,
          "r_engine_stats": {
            "pages_accessed": 5
          },
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100
        }
      }
    ]
  }
}
```


With FORCE INDEX (idx_hosp_dept)

```json 
{
  "query_optimization": {
    "r_total_time_ms": 0.678509021
  },
  "query_block": {
    "select_id": 1,
    "cost": 3.254048857,
    "r_loops": 1,
    "r_total_time_ms": 1.720397819,
    "filesort": {
      "sort_key": "h.`id`",
      "r_loops": 1,
      "r_total_time_ms": 0.013833081,
      "r_used_priority_queue": false,
      "r_output_rows": 3,
      "r_buffer_size": "304",
      "r_sort_mode": "sort_key,rowid",
      "temporary_table": {
        "nested_loop": [
          {
            "table": {
              "table_name": "d",
              "access_type": "index",
              "possible_keys": ["PRIMARY"],
              "key": "uq_department_name",
              "key_length": "402",
              "used_key_parts": ["name"],
              "loops": 1,
              "r_loops": 1,
              "rows": 15,
              "r_rows": 15,
              "cost": 0.008846195,
              "r_table_time_ms": 0.033606897,
              "r_other_time_ms": 0.021077943,
              "r_engine_stats": {
                "pages_accessed": 1
              },
              "filtered": 100,
              "r_total_filtered": 100,
              "r_filtered": 100,
              "using_index": true
            }
          },
          {
            "table": {
              "table_name": "h",
              "access_type": "ref",
              "possible_keys": ["idx_hosp_dept"],
              "key": "idx_hosp_dept",
              "key_length": "4",
              "used_key_parts": ["department_id"],
              "ref": ["ygeiopolis.d.id"],
              "loops": 15,
              "r_loops": 15,
              "rows": 33,
              "r_rows": 33.33333333,
              "cost": 0.5082496,
              "r_table_time_ms": 1.32556943,
              "r_other_time_ms": 0.114060353,
              "r_engine_stats": {
                "pages_accessed": 1015
              },
              "filtered": 100,
              "r_total_filtered": 0.6,
              "attached_condition": "h.patient_amka = '00545228015'",
              "r_filtered": 0.6
            }
          },
          {
            "table": {
              "table_name": "kc",
              "access_type": "eq_ref",
              "possible_keys": ["PRIMARY"],
              "key": "PRIMARY",
              "key_length": "42",
              "used_key_parts": ["code"],
              "ref": ["ygeiopolis.h.ken_code"],
              "loops": 495,
              "r_loops": 3,
              "rows": 1,
              "r_rows": 1,
              "cost": 0.4673238,
              "r_table_time_ms": 0.027847546,
              "r_other_time_ms": 0.006951858,
              "r_engine_stats": {
                "pages_accessed": 7
              },
              "filtered": 100,
              "r_total_filtered": 100,
              "r_filtered": 100
            }
          },
          {
            "table": {
              "table_name": "icd_adm",
              "access_type": "eq_ref",
              "possible_keys": ["PRIMARY"],
              "key": "PRIMARY",
              "key_length": "42",
              "used_key_parts": ["code"],
              "ref": ["ygeiopolis.h.admission_icd10"],
              "loops": 495,
              "r_loops": 3,
              "rows": 1,
              "r_rows": 1,
              "cost": 0.5222102,
              "r_table_time_ms": 0.021683571,
              "r_other_time_ms": 0.005591048,
              "r_engine_stats": {
                "pages_accessed": 6
              },
              "filtered": 100,
              "r_total_filtered": 100,
              "r_filtered": 100
            }
          },
          {
            "table": {
              "table_name": "icd_dis",
              "access_type": "eq_ref",
              "possible_keys": ["PRIMARY"],
              "key": "PRIMARY",
              "key_length": "42",
              "used_key_parts": ["code"],
              "ref": ["ygeiopolis.h.discharge_icd10"],
              "loops": 495,
              "r_loops": 3,
              "rows": 1,
              "r_rows": 1,
              "cost": 0.5222102,
              "r_table_time_ms": 0.016294834,
              "r_other_time_ms": 0.007381335,
              "r_engine_stats": {
                "pages_accessed": 6
              },
              "filtered": 100,
              "r_total_filtered": 100,
              "attached_condition": "trigcond(trigcond(h.discharge_icd10 is not null))",
              "r_filtered": 100
            }
          },
          {
            "table": {
              "table_name": "prh",
              "access_type": "ref",
              "possible_keys": ["uq_rev_hosp", "idx_rev_hosp_hosp"],
              "key": "uq_rev_hosp",
              "key_length": "4",
              "used_key_parts": ["hospitalization_id"],
              "ref": ["ygeiopolis.h.id"],
              "loops": 495,
              "r_loops": 3,
              "rows": 1,
              "r_rows": 0.666666667,
              "cost": 0.9026176,
              "r_table_time_ms": 0.022092991,
              "r_other_time_ms": 0.071121816,
              "r_engine_stats": {
                "pages_accessed": 5
              },
              "filtered": 100,
              "r_total_filtered": 100,
              "r_filtered": 100
            }
          }
        ]
      }
    }
  }
}
```

## C) Comparison of estimated cost and actual execution time

- **Estimated cost:** 0.033108 → 3.254049 (≈ 98× increase).
- **Actual total time (top-level):** 0.2168 ms → 0.6785 ms (≈ 3.1× slower).
- **Query-block time:** 0.1257 ms → 1.7204 ms (≈ 13.7× slower).

## D) Short analysis

- Forcing `idx_hosp_dept` pushed the optimizer onto a low-selectivity access path, dramatically increasing scanned rows, page accesses and causing a temporary filesort.
- The planner's cost estimate rose by about two orders of magnitude and the measured execution times increased substantially, validating the optimizer's warning.
- Conclusion: do not force `idx_hosp_dept` for this query; allow the optimizer to use `idx_hosp_patient` or introduce a more appropriate composite index if needed.