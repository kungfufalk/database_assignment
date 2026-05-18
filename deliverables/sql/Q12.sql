SELECT
    d.name AS department_name,
    s.shift_date,
    s.shift_type,
    st.staff_type,
    CASE
        WHEN st.staff_type = 'doctor' THEN doc.specialty
        WHEN st.staff_type = 'nurse' THEN n.rank
        WHEN st.staff_type = 'admin' THEN a.role
        ELSE 'Other'
    END AS personnel_subclass,
    COUNT(sa.staff_amka) AS total_personnel_required
FROM
    shift s
    JOIN department d ON s.department_id = d.id
    JOIN shift_assignment sa ON s.id = sa.shift_id
    JOIN staff st ON sa.staff_amka = st.amka
    LEFT JOIN doctor doc ON st.amka = doc.amka
    LEFT JOIN nurse n ON st.amka = n.amka
    LEFT JOIN admin_staff a ON st.amka = a.amka
WHERE
    s.shift_date BETWEEN '2025-01-06'
    AND '2025-01-12'
GROUP BY
    d.name,
    s.shift_date,
    s.shift_type,
    st.staff_type,
    personnel_subclass
LIMIT
    100;