WITH RECURSIVE supervision_path AS (
    -- Anchor Member: Start with the top-level Directors (no supervisor)
    SELECT 
        d.amka AS doctor_amka,
        d.supervisor_amka,
        d.rank,
        CAST(CONCAT(st.first_name, ' ', st.last_name) AS CHAR(1000)) AS hierarchy_path,
        1 AS hierarchy_level
    FROM doctor d
    JOIN staff st 
        ON d.amka = st.amka
    WHERE d.supervisor_amka IS NULL

    UNION ALL

    -- Recursive Member: Join remaining doctors to their supervisors already in the CTE
    SELECT 
        e.amka AS doctor_amka,
        e.supervisor_amka,
        e.rank,
        CONCAT(s.hierarchy_path, ' -> ', st_e.first_name, ' ', st_e.last_name) AS hierarchy_path,
        s.hierarchy_level + 1 AS hierarchy_level
    FROM doctor e
    JOIN staff st_e 
        ON e.amka = st_e.amka
    INNER JOIN supervision_path s 
        ON e.supervisor_amka = s.doctor_amka
)
SELECT 
    doctor_amka,
    rank AS doctor_rank,
    hierarchy_level,
    hierarchy_path
FROM supervision_path
ORDER BY 
    hierarchy_level, 
    hierarchy_path;