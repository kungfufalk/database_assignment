SELECT
    d.name AS department,
    sh.shift_date,
    sh.shift_type,
    s.staff_type,
    CASE s.staff_type
        WHEN 'doctor' THEN doc.specialty
        WHEN 'nurse' THEN n.rank
        WHEN 'admin' THEN a.role
    END AS sub_category,
    COUNT(sa.id) AS staff_count
FROM
    shift sh
    JOIN department d ON d.id = sh.department_id
    JOIN shift_assignment sa ON sa.shift_id = sh.id
    JOIN staff s ON s.amka = sa.staff_amka
    LEFT JOIN doctor doc ON doc.amka = s.amka
    LEFT JOIN nurse n ON n.amka = s.amka
    LEFT JOIN admin_staff a ON a.amka = s.amka
WHERE
    sh.shift_date BETWEEN '2025-01-13' AND '2025-01-19'
GROUP BY
    d.id,
    d.name,
    sh.shift_date,
    sh.shift_type,
    s.staff_type,
    CASE s.staff_type
        WHEN 'doctor' THEN doc.specialty
        WHEN 'nurse' THEN n.rank
        WHEN 'admin' THEN a.role
    END
ORDER BY
    sh.shift_date,
    d.name,
    sh.shift_type,
    s.staff_type,
    sub_category;