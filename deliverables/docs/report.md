## Assumptions
- the category of the IDC10-code is infront of the dot
- the category of the KEN-code is the first latter of the code
- we used the birthdate instead of age in patient table, so we dont have to change it every year
- we left out the constraints on the staffed department shift, because it was to complicated to check -> unfortunately SQL does not allow aggregates on constraints -> in a real system this needs to be covered from the business logic, to make the data consistent
- the serving queue (urgency level + FIFO) should not be handled by the database, but by the system which uses the database
- the propotional additional daily charge in our case will be calculated by base cost divided by the days. This Information will be calculated from the business logic
- we interpreted the query 9 the following way: find all patient and year combinations where: total hospitalization days exceed 15 and that total is shared by at least one other patient and year combination

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