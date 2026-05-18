SELECT
    t.urgency_level,
    COUNT(*) AS total_cases,
    ROUND(
        AVG(
            TIMESTAMPDIFF (MINUTE, t.arrival_time, t.service_time)
        ),
        1
    ) AS avg_wait_min,
    ROUND(
        (
            COUNT(
                CASE
                    WHEN t.outcome = 'Admitted' THEN 1
                END
            ) / COUNT(*)
        ) * 100,
        2
    ) AS admission_pct,
    COALESCE(
        GROUP_CONCAT (
            DISTINCT CONCAT (
                d.name,
                ': ',
                (
                    SELECT
                        COUNT(*)
                    FROM
                        hospitalization h2
                    WHERE
                        h2.triage_id IS NOT NULL
                        AND h2.department_id = d.id
                        AND h2.patient_amka = t.patient_amka
                )
            ) SEPARATOR ', '
        ),
        'None'
    ) AS dept_referrals
FROM
    triage t
    LEFT JOIN hospitalization h ON t.id = h.triage_id
    LEFT JOIN department d ON h.department_id = d.id
GROUP BY
    t.urgency_level
ORDER BY
    t.urgency_level;