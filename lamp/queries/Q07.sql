-- For each active substance, find the number of patients who have declared an allergy to it and the
-- number of medications containing it, sorted by total number of allergic patients.

-- Output: line of active substance with addiotional information
-- Involved tables: drug -- drug_active_substance -- active_substance -- patient_allergy
SELECT
sub.id,
sub.name,
allergy_counts.num_pat,
drug_count.num_drug
FROM active_substance sub
LEFT JOIN (
    SELECT
        substance_id,
        COUNT(DISTINCT patient_amka) AS num_pat
    FROM patient_allergy
    GROUP BY substance_id
) AS allergy_counts ON allergy_counts.substance_id = sub.id
LEFT JOIN
(
    SELECT
    sub.id as sub_id,
    COUNT(*) as num_drug
    FROM
    active_substance sub
    JOIN drug_active_substance drug_sub on drug_sub.substance_id = sub.id
    GROUP BY sub.id
) as drug_count
on drug_count.sub_id = sub.id
ORDER BY
    allergy_counts.num_pat DESC,
    drug_count.num_drug DESC;