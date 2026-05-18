SELECT
    hospitalization_cost.patient_amka,
    SUM(
        CASE
            WHEN hospitalization_cost.hosp_days > hospitalization_cost.mean_los_days THEN hospitalization_cost.base_cost + (
                hospitalization_cost.hosp_days - hospitalization_cost.mean_los_days
            ) * (
                hospitalization_cost.base_cost / hospitalization_cost.mean_los_days
            )
            ELSE hospitalization_cost.base_cost
        END
    ) AS total_cost
FROM
    (
        SELECT
            h.ken_code,
            h.patient_amka,
            h.department_id,
            TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date) AS hosp_days,
            k.base_cost,
            k.mean_los_days
        FROM
            hospitalization h
            JOIN ken_code k ON k.code = h.ken_code
    ) AS hospitalization_cost
WHERE
    hospitalization_cost.patient_amka IN (
        SELECT
            patient_amka
        FROM
            hospitalization
        GROUP BY
            patient_amka,
            department_id
        HAVING
            COUNT(department_id) > 3
    )
GROUP BY
    hospitalization_cost.patient_amka
ORDER BY
    hospitalization_cost.patient_amka;