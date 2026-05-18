WITH
    triage_stats AS (
        SELECT
            t.urgency_level,
            COUNT(*) AS total_cases,
            SUM(
                CASE
                    WHEN t.outcome = 'Admitted' THEN 1
                    ELSE 0
                END
            ) AS admitted_count,
            AVG(
                CASE
                    WHEN t.service_time IS NOT NULL THEN TIMESTAMPDIFF (MINUTE, t.arrival_time, t.service_time)
                    ELSE NULL
                END
            ) AS avg_wait_minutes
        FROM
            triage t
        GROUP BY
            t.urgency_level
    ),
    referrals_by_dept AS (
        SELECT
            t.urgency_level,
            d.name AS department,
            COUNT(*) AS referral_count
        FROM
            triage t
            JOIN hospitalization h ON h.triage_id = t.id
            JOIN department d ON d.id = h.department_id
        WHERE
            t.outcome = 'Admitted'
        GROUP BY
            t.urgency_level,
            h.department_id,
            d.name
    )
SELECT
    ts.urgency_level,
    CASE ts.urgency_level
        WHEN 1 THEN 'Immediate'
        WHEN 2 THEN 'Emergent'
        WHEN 3 THEN 'Urgent'
        WHEN 4 THEN 'Less Urgent'
        WHEN 5 THEN 'Non-Urgent'
    END AS urgency_label,
    ts.total_cases,
    ROUND(ts.avg_wait_minutes, 1) AS avg_wait_minutes,
    ts.admitted_count,
    ROUND(ts.admitted_count * 100.0 / ts.total_cases, 2) AS pct_admitted,
    rd.department,
    rd.referral_count
FROM
    triage_stats ts
    LEFT JOIN referrals_by_dept rd ON rd.urgency_level = ts.urgency_level
ORDER BY
    ts.urgency_level,
    rd.referral_count DESC;