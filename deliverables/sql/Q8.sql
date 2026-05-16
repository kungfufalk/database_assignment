SELECT
    staff.amka,
    staff.first_name,
    staff.last_name
FROM
    staff
WHERE
    staff.amka NOT IN (
        SELECT
            staff.amka
        FROM
            staff
            JOIN shift_assignment sa ON staff.amka = sa.staff_amka
            JOIN shift s ON sa.shift_id = s.id
            JOIN department d ON s.department_id = d.id
        WHERE
            s.shift_date = '2025-01-01'
            AND d.name = 'Γαστρεντερολογική Κλινική'
            AND s.shift_type = 'Night'
        GROUP BY
            staff.amka
    );