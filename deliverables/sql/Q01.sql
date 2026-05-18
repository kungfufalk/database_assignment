SELECT
    d.name AS department,
    YEAR (h.admission_date) AS year,
    h.ken_code,
    k.description AS ken_description,
    COUNT(h.id) AS total_hospitalizations,
    SUM(k.base_cost) AS total_base_cost,
    SUM(
        CASE
            WHEN TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date) > k.mean_los_days THEN TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date) - k.mean_los_days * (k.base_cost / k.mean_los_days)
            ELSE 0
        END
    ) AS total_surcharge,
    SUM(
        CASE
            WHEN TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date) > k.mean_los_days THEN k.base_cost + (
                TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date) - k.mean_los_days
            ) * (k.base_cost / k.mean_los_days)
            ELSE k.base_cost
        END
    ) AS total_revenue,
    SUM(
        CASE
            WHEN p.insurance = 'EFKA' THEN 1
            ELSE 0
        END
    ) AS count_efka,
    SUM(
        CASE
            WHEN p.insurance = 'Private' THEN 1
            ELSE 0
        END
    ) AS count_private,
    SUM(
        CASE
            WHEN p.insurance = 'Uninsured' THEN 1
            ELSE 0
        END
    ) AS count_uninsured,
    SUM(
        CASE
            WHEN p.insurance = 'Other' THEN 1
            ELSE 0
        END
    ) AS count_other
FROM
    hospitalization h
    JOIN department d ON d.id = h.department_id
    JOIN ken_code k ON k.code = h.ken_code
    JOIN patient p ON p.amka = h.patient_amka
GROUP BY
    d.id,
    d.name,
    YEAR (h.admission_date),
    h.ken_code,
    k.description
ORDER BY
    year DESC,
    department,
    total_revenue DESC;