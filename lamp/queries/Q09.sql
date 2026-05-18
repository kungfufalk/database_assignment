SELECT
    p.amka,
    p.first_name,
    p.last_name,
    YEAR (h.admission_date) AS hosp_year,
    SUM(
        TIMESTAMPDIFF (DAY, h.admission_date, h.discharge_date)
    ) AS total_days
FROM
    patient p
    JOIN hospitalization h ON h.patient_amka = p.amka
GROUP BY
    p.amka,
    YEAR (h.admission_date)
HAVING
    total_days > 15
    AND total_days IN (
        SELECT
            long_hosp.total_days
        FROM
            (
                SELECT
                    SUM(
                        TIMESTAMPDIFF (DAY, admission_date, discharge_date)
                    ) as total_days
                FROM
                    hospitalization
                GROUP BY
                    patient_amka,
                    YEAR (admission_date)
                HAVING
                    SUM(
                        TIMESTAMPDIFF (DAY, admission_date, discharge_date)
                    ) > 15
            ) as long_hosp
        GROUP BY
            long_hosp.total_days
        HAVING
            COUNT(*) > 1
    )
ORDER BY
    total_days ASC