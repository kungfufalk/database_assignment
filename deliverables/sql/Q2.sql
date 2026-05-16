SELECT
    d.amka,
    st.first_name,
    st.last_name,
    CASE
        WHEN COUNT(DISTINCT sh.id) > 0 THEN 'Yes'
        ELSE 'No'
    END AS had_oncall_this_year,
    COUNT(DISTINCT mp.id) AS lead_procedures
FROM
    doctor d
    JOIN staff st ON st.amka = d.amka
    LEFT JOIN medical_procedure mp ON mp.primary_surgeon_amka = d.amka
    LEFT JOIN shift_assignment sa ON sa.staff_amka = d.amka
    LEFT JOIN shift sh ON sh.id = sa.shift_id
    AND sh.shift_type = 'Night'
    AND YEAR(sh.shift_date) = YEAR(CURDATE()) -1
WHERE
    d.specialty = 'Surgery'
GROUP BY
    d.amka,
    st.first_name,
    st.last_name;