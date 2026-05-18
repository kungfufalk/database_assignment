WITH
    admissions_per_category_year AS (
        SELECT
            LEFT (h.admission_icd10, 3) AS icd_category,
            YEAR (h.admission_date) AS year,
            COUNT(*) AS admission_count
        FROM
            hospitalization h
        GROUP BY
            LEFT (h.admission_icd10, 3),
            YEAR (h.admission_date)
        HAVING
            COUNT(*) >= 5
    )
SELECT
    a1.icd_category,
    a1.year AS year_1,
    a2.year AS year_2,
    a1.admission_count AS admissions_year_1,
    a2.admission_count AS admissions_year_2
FROM
    admissions_per_category_year a1
    JOIN admissions_per_category_year a2 ON a2.icd_category = a1.icd_category
    AND a2.year = a1.year + 1 -- consecutive years
    AND a2.admission_count = a1.admission_count -- same count
ORDER BY
    a1.icd_category,
    a1.year;