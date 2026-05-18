WITH RECURSIVE
    supervision_chain AS (
        SELECT
            d.amka AS doctor_amka,
            d.amka AS current_amka,
            d.supervisor_amka AS supervisor_amka,
            d.rank AS current_rank,
            0 AS level,
            CAST(d.amka AS CHAR(1000)) AS path
        FROM
            doctor d
        UNION ALL
        SELECT
            sc.doctor_amka,
            d.amka,
            d.supervisor_amka,
            d.rank,
            sc.level + 1,
            CONCAT (sc.path, ' -> ', d.amka)
        FROM
            supervision_chain sc
            JOIN doctor d ON d.amka = sc.supervisor_amka
        WHERE
            sc.supervisor_amka IS NOT NULL
    )
SELECT
    s_doc.first_name AS doctor_first_name,
    s_doc.last_name AS doctor_last_name,
    d_doc.rank AS doctor_rank,
    d_doc.specialty AS doctor_specialty,
    sc.level AS hierarchy_level,
    s_sup.first_name AS supervisor_first_name,
    s_sup.last_name AS supervisor_last_name,
    d_sup.rank AS supervisor_rank,
    d_sup.specialty AS supervisor_specialty,
    sc.path AS full_chain
FROM
    supervision_chain sc
    JOIN doctor d_doc ON d_doc.amka = sc.doctor_amka
    JOIN staff s_doc ON s_doc.amka = sc.doctor_amka
    JOIN doctor d_sup ON d_sup.amka = sc.current_amka
    JOIN staff s_sup ON s_sup.amka = sc.current_amka
WHERE
    sc.level > 0
ORDER BY
    s_doc.last_name,
    s_doc.first_name,
    sc.level;