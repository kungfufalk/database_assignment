WITH
    t AS (
        SELECT
            d.amka,
            COUNT(DISTINCT md.id) AS nr_procedures
        FROM
            doctor d
            JOIN procedure_staff ps ON d.amka = ps.staff_amka
            JOIN medical_procedure md ON ps.procedure_id = md.id
            OR d.amka = md.primary_surgeon_amka
        WHERE
            YEAR (md.start_datetime) = YEAR (CURRENT_DATE()) - 2
        GROUP BY
            d.amka
    )
SELECT
    t.amka,
    s.first_name,
    s.last_name
FROM
    t
    JOIN staff s ON t.amka = s.amka
WHERE
    t.nr_procedures > (
        SELECT
            MAX(t.nr_procedures) - 5
        FROM
            t
    );