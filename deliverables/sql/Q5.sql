SELECT
    staff.amka,
    staff.first_name,
    staff.last_name,
    TIMESTAMPDIFF (YEAR, staff.birth_date, CURRENT_DATE()) as 'age',
    COUNT(mp.id) AS 'Lead'
FROM
    doctor d
    JOIN staff ON d.amka = staff.amka
    JOIN medical_procedure mp ON d.amka = mp.primary_surgeon_amka
WHERE
    TIMESTAMPDIFF (YEAR, staff.birth_date, CURRENT_DATE()) < 35
GROUP BY
    staff.amka,
    staff.first_name,
    staff.last_name,
    'age'
ORDER BY
    Lead DESC
LIMIT
    1;