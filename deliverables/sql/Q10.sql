WITH
    hospitalization_substances AS (
        SELECT DISTINCT
            pr.hospitalization_id,
            pr.patient_amka,
            das.substance_id
        FROM
            prescription pr
            JOIN drug_active_substance das ON das.drug_id = pr.drug_id
    ),
    substance_pairs AS (
        SELECT
            hs1.hospitalization_id,
            hs1.substance_id AS substance_id_1,
            hs2.substance_id AS substance_id_2
        FROM
            hospitalization_substances hs1
            JOIN hospitalization_substances hs2 ON hs2.hospitalization_id = hs1.hospitalization_id
            AND hs2.patient_amka = hs1.patient_amka
            AND hs2.substance_id > hs1.substance_id
    )
SELECT
    a1.name AS substance_1,
    a2.name AS substance_2,
    COUNT(*) AS co_prescription_count
FROM
    substance_pairs sp
    JOIN active_substance a1 ON a1.id = sp.substance_id_1
    JOIN active_substance a2 ON a2.id = sp.substance_id_2
GROUP BY
    sp.substance_id_1,
    sp.substance_id_2,
    a1.name,
    a2.name
ORDER BY
    co_prescription_count DESC
LIMIT
    3;