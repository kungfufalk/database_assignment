SELECT
    h.id,
    d.name AS department_name,
    h.admission_icd10,
    icd_adm.description AS admission_diagnosis,
    h.discharge_icd10,
    icd_dis.description AS discharge_diagnosis,
    ROUND(
        kc.base_cost + CASE
            WHEN DATEDIFF (
                IFNULL (h.discharge_date, CURDATE ()),
                h.admission_date
            ) > kc.mean_los_days THEN (
                DATEDIFF (
                    IFNULL (h.discharge_date, CURDATE ()),
                    h.admission_date
                ) - kc.mean_los_days
            ) * (kc.base_cost / kc.mean_los_days)
            ELSE 0
        END,
        2
    ) AS total_cost,
    ROUND(
        AVG(
            (
                prh.nursing_care + prh.cleanliness + prh.food + prh.overall_experience
            ) / 4.0
        ),
        2
    ) AS avg_hospitalization_evaluation
FROM
    hospitalization h
    JOIN department d ON h.department_id = d.id
    JOIN ken_code kc ON h.ken_code = kc.code
    JOIN icd10_code icd_adm ON h.admission_icd10 = icd_adm.code
    LEFT JOIN icd10_code icd_dis ON h.discharge_icd10 = icd_dis.code
    LEFT JOIN patient_review_hospitalization prh ON h.id = prh.hospitalization_id
WHERE
    h.patient_amka = '00545228015'
GROUP BY
    h.id;