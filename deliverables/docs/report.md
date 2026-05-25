## Assumptions
- the category of the IDC10-code is infront of the dot
- the category of the KEN-code is the first latter of the code
- we used the birthdate instead of age in patient table, so we dont have to change it every year
- we left out the constraints on the staffed department shift, because it was to complicated to check -> unfortunately SQL does not allow aggregates on constraints -> in a real system this needs to be covered from the business logic, to make the data consistent
- the serving queue (urgency level + FIFO) should not be handled by the database, but by the system which uses the database
- the propotional additional daily charge in our case will be calculated by base cost divided by the days. This Information will be calculated from the business logic
- we interpreted the query 9 the following way: find all patient and year combinations where: total hospitalization days exceed 15 and that total is shared by at least one other patient and year combination

## Indexes — Justifications

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


## Query 4 analysation
Output without force index:
``` json
{
  "query_optimization": {
    "r_total_time_ms": 0.211495327
  },
  "query_block": {
    "select_id": 1,
    "cost": 0.020416784,
    "r_loops": 1,
    "r_total_time_ms": 0.073843564,
    "const_condition": "1",
    "nested_loop": [
      {
        "table": {
          "table_name": "d",
          "access_type": "const",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "44",
          "used_key_parts": ["amka"],
          "ref": ["const"],
          "r_loops": 0,
          "rows": 1,
          "r_rows": null,
          "r_engine_stats": {
            "pages_accessed": 1
          },
          "filtered": 100,
          "r_total_filtered": null,
          "r_filtered": null
        }
      },
      {
        "table": {
          "table_name": "s",
          "access_type": "const",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "44",
          "used_key_parts": ["amka"],
          "ref": ["const"],
          "r_loops": 0,
          "rows": 1,
          "r_rows": null,
          "r_engine_stats": {
            "pages_accessed": 2
          },
          "filtered": 100,
          "r_total_filtered": null,
          "r_filtered": null
        }
      },
      {
        "table": {
          "table_name": "<derived2>",
          "access_type": "ref",
          "possible_keys": ["key0"],
          "key": "key0",
          "key_length": "45",
          "used_key_parts": ["doctor_amka"],
          "ref": ["const"],
          "loops": 1,
          "r_loops": 1,
          "rows": 0,
          "r_rows": 1,
          "cost": 0.00605097,
          "r_table_time_ms": 0.009868109,
          "r_other_time_ms": 0.005268567,
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100,
          "materialized": {
            "lateral": 1,
            "query_block": {
              "select_id": 2,
              "cost": 0.005715537,
              "r_loops": 1,
              "r_total_time_ms": 0.026008322,
              "nested_loop": [
                {
                  "table": {
                    "table_name": "patient_review_doctor",
                    "access_type": "ref",
                    "possible_keys": ["idx_rev_doctor_doctor"],
                    "key": "idx_rev_doctor_doctor",
                    "key_length": "44",
                    "used_key_parts": ["doctor_amka"],
                    "ref": ["const"],
                    "loops": 1,
                    "r_loops": 1,
                    "rows": 2,
                    "r_index_rows": 2,
                    "r_rows": 2,
                    "cost": 0.004452,
                    "r_table_time_ms": 0.008028292,
                    "r_other_time_ms": 0.006732058,
                    "r_engine_stats": {
                      "pages_accessed": 3
                    },
                    "filtered": 100,
                    "r_total_filtered": 100,
                    "index_condition": "patient_review_doctor.doctor_amka = '00330923271'",
                    "r_icp_filtered": 100,
                    "r_filtered": 100
                  }
                }
              ]
            }
          }
        }
      },
      {
        "table": {
          "table_name": "<derived3>",
          "access_type": "ref",
          "possible_keys": ["key0"],
          "key": "key0",
          "key_length": "45",
          "used_key_parts": ["doctor_amka"],
          "ref": ["const"],
          "loops": 1,
          "r_loops": 1,
          "rows": 0,
          "r_rows": 1,
          "cost": 0.014365814,
          "r_table_time_ms": 0.009575411,
          "r_other_time_ms": 0.001045351,
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100,
          "materialized": {
            "lateral": 1,
            "query_block": {
              "select_id": 3,
              "cost": 0.019954568,
              "r_loops": 1,
              "r_total_time_ms": 0.038092575,
              "nested_loop": [
                {
                  "table": {
                    "table_name": "pr",
                    "access_type": "ref",
                    "possible_keys": [
                      "uq_prescription",
                      "idx_presc_hosp",
                      "idx_presc_patient",
                      "idx_presc_doctor"
                    ],
                    "key": "uq_prescription",
                    "key_length": "44",
                    "used_key_parts": ["doctor_amka"],
                    "ref": ["const"],
                    "loops": 1,
                    "r_loops": 1,
                    "rows": 4,
                    "r_index_rows": 4,
                    "r_rows": 4,
                    "cost": 0.00889648,
                    "r_table_time_ms": 0.009659039,
                    "r_other_time_ms": 0.00426503,
                    "r_engine_stats": {
                      "pages_accessed": 9
                    },
                    "filtered": 100,
                    "r_total_filtered": 100,
                    "index_condition": "pr.doctor_amka = '00330923271'",
                    "r_icp_filtered": 100,
                    "r_filtered": 100
                  }
                },
                {
                  "table": {
                    "table_name": "rh",
                    "access_type": "eq_ref",
                    "possible_keys": [
                      "uq_rev_hosp",
                      "idx_rev_hosp_hosp",
                      "idx_rev_hosp_patient"
                    ],
                    "key": "uq_rev_hosp",
                    "key_length": "48",
                    "used_key_parts": ["hospitalization_id", "patient_amka"],
                    "ref": [
                      "ygeiopolis.pr.hospitalization_id",
                      "ygeiopolis.pr.patient_amka"
                    ],
                    "loops": 4,
                    "r_loops": 4,
                    "rows": 1,
                    "r_rows": 0.5,
                    "cost": 0.00852304,
                    "r_table_time_ms": 0.006397545,
                    "r_other_time_ms": 0.00706657,
                    "r_engine_stats": {
                      "pages_accessed": 6
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
    ]
  }
}
```

Output with forced index on `FROM prescription pr FORCE INDEX (idx_presc_doctor)`
``` json
{
  "query_optimization": {
    "r_total_time_ms": 0.711089271
  },
  "query_block": {
    "select_id": 1,
    "cost": 0.020416784,
    "r_loops": 1,
    "r_total_time_ms": 0.316783036,
    "const_condition": "1",
    "nested_loop": [
      {
        "table": {
          "table_name": "d",
          "access_type": "const",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "44",
          "used_key_parts": ["amka"],
          "ref": ["const"],
          "r_loops": 0,
          "rows": 1,
          "r_rows": null,
          "r_engine_stats": {
            "pages_accessed": 1
          },
          "filtered": 100,
          "r_total_filtered": null,
          "r_filtered": null
        }
      },
      {
        "table": {
          "table_name": "s",
          "access_type": "const",
          "possible_keys": ["PRIMARY"],
          "key": "PRIMARY",
          "key_length": "44",
          "used_key_parts": ["amka"],
          "ref": ["const"],
          "r_loops": 0,
          "rows": 1,
          "r_rows": null,
          "r_engine_stats": {
            "pages_accessed": 2
          },
          "filtered": 100,
          "r_total_filtered": null,
          "r_filtered": null
        }
      },
      {
        "table": {
          "table_name": "<derived2>",
          "access_type": "ref",
          "possible_keys": ["key0"],
          "key": "key0",
          "key_length": "45",
          "used_key_parts": ["doctor_amka"],
          "ref": ["const"],
          "loops": 1,
          "r_loops": 1,
          "rows": 0,
          "r_rows": 1,
          "cost": 0.00605097,
          "r_table_time_ms": 0.026677347,
          "r_other_time_ms": 0.016474725,
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100,
          "materialized": {
            "lateral": 1,
            "query_block": {
              "select_id": 2,
              "cost": 0.005715537,
              "r_loops": 1,
              "r_total_time_ms": 0.102737054,
              "nested_loop": [
                {
                  "table": {
                    "table_name": "patient_review_doctor",
                    "access_type": "ref",
                    "possible_keys": ["idx_rev_doctor_doctor"],
                    "key": "idx_rev_doctor_doctor",
                    "key_length": "44",
                    "used_key_parts": ["doctor_amka"],
                    "ref": ["const"],
                    "loops": 1,
                    "r_loops": 1,
                    "rows": 2,
                    "r_index_rows": 2,
                    "r_rows": 2,
                    "cost": 0.004452,
                    "r_table_time_ms": 0.053312879,
                    "r_other_time_ms": 0.016223841,
                    "r_engine_stats": {
                      "pages_accessed": 3
                    },
                    "filtered": 100,
                    "r_total_filtered": 100,
                    "index_condition": "patient_review_doctor.doctor_amka = '00330923271'",
                    "r_icp_filtered": 100,
                    "r_filtered": 100
                  }
                }
              ]
            }
          }
        }
      },
      {
        "table": {
          "table_name": "<derived3>",
          "access_type": "ref",
          "possible_keys": ["key0"],
          "key": "key0",
          "key_length": "45",
          "used_key_parts": ["doctor_amka"],
          "ref": ["const"],
          "loops": 1,
          "r_loops": 1,
          "rows": 0,
          "r_rows": 1,
          "cost": 0.014365814,
          "r_table_time_ms": 0.009240899,
          "r_other_time_ms": 0.004892241,
          "filtered": 100,
          "r_total_filtered": 100,
          "r_filtered": 100,
          "materialized": {
            "lateral": 1,
            "query_block": {
              "select_id": 3,
              "cost": 0.019954568,
              "r_loops": 1,
              "r_total_time_ms": 0.178922203,
              "nested_loop": [
                {
                  "table": {
                    "table_name": "pr",
                    "access_type": "ref",
                    "possible_keys": ["idx_presc_doctor"],
                    "key": "idx_presc_doctor",
                    "key_length": "44",
                    "used_key_parts": ["doctor_amka"],
                    "ref": ["const"],
                    "loops": 1,
                    "r_loops": 1,
                    "rows": 4,
                    "r_index_rows": 4,
                    "r_rows": 4,
                    "cost": 0.00889648,
                    "r_table_time_ms": 0.101524447,
                    "r_other_time_ms": 0.018105472,
                    "r_engine_stats": {
                      "pages_accessed": 9
                    },
                    "filtered": 100,
                    "r_total_filtered": 100,
                    "index_condition": "pr.doctor_amka = '00330923271'",
                    "r_icp_filtered": 100,
                    "r_filtered": 100
                  }
                },
                {
                  "table": {
                    "table_name": "rh",
                    "access_type": "eq_ref",
                    "possible_keys": [
                      "uq_rev_hosp",
                      "idx_rev_hosp_hosp",
                      "idx_rev_hosp_patient"
                    ],
                    "key": "uq_rev_hosp",
                    "key_length": "48",
                    "used_key_parts": ["hospitalization_id", "patient_amka"],
                    "ref": [
                      "ygeiopolis.pr.hospitalization_id",
                      "ygeiopolis.pr.patient_amka"
                    ],
                    "loops": 4,
                    "r_loops": 4,
                    "rows": 1,
                    "r_rows": 0.5,
                    "cost": 0.00852304,
                    "r_table_time_ms": 0.035583733,
                    "r_other_time_ms": 0.009073643,
                    "r_engine_stats": {
                      "pages_accessed": 6
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
    ]
  }
}
```

We chose to force the index `idx_presc_doctor` on the query 4, because the prescription table has multiple competing indexes and we want to compare the optimisers choice of index `uq_prescription`.
After forcing the index `idx_presc_doctor` we can see a longer query time.
`uq_prescription` : 0.211 ms
`idx_presc_doctor` : 0.711ms
Overriding the optimisers cost-based selection leads to suboptimal access path.
What is interesting, that both versions show the same estimated cost, so the optimiser thinks they are equally cheap. This might be misleading and we can see the actual difference in the execution time. The optimiser does not always choose the best real time index, which needs to be kept in mind in case of execution time issues and sometimes deeper analysation might be required.


## Q6 Analysis
### a) Analyze output 
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

### C) Comparison of estimated cost and actual execution time

- **Estimated cost:** 0.033108 → 3.254049 (≈ 98× increase).
- **Actual total time (top-level):** 0.2168 ms → 0.6785 ms (≈ 3.1× slower).
- **Query-block time:** 0.1257 ms → 1.7204 ms (≈ 13.7× slower).

### D) Short analysis

- Forcing `idx_hosp_dept` pushed the optimizer onto a low-selectivity access path, dramatically increasing scanned rows, page accesses and causing a temporary filesort.
- The planner's cost estimate rose by about two orders of magnitude and the measured execution times increased substantially, validating the optimizer's warning.
- Conclusion: do not force `idx_hosp_dept` for this query; allow the optimizer to use `idx_hosp_patient` or introduce a more appropriate composite index if needed.

## Use of AI tools 
AI tools were used throughout the exercise to support research, idea development, organization, and refinement of the final work. Their use helped improve efficiency and clarity while maintaining critical evaluation and personal input during the process.