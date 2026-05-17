SELECT
    prd.doctor_amka,
    s.first_name,
    s.last_name,
    COUNT(DISTINCT prd.id) AS reviews,
    AVG(prd.medical_care) AS avg_medical_care_rating,
    AVG(prh.overall_experience) AS avg_overall_experience
FROM
    patient_review_doctor prd
    JOIN staff s ON prd.doctor_amka = s.amka
    JOIN patient_review_hospitalization prh ON prd.hospitalization_id = prh.hospitalization_id
    AND prd.patient_amka = prh.patient_amka
WHERE
    prd.doctor_amka = '00330923271'
GROUP BY
    prd.doctor_amka;