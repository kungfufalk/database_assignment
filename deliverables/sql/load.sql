LOAD DATA LOCAL INFILE '/var/lib/mysql-files/icd10_code.csv'
INTO TABLE icd10_code
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

LOAD DATA LOCAL INFILE '/var/lib/mysql-files/ken_code.csv'
INTO TABLE ken_code
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

LOAD DATA LOCAL INFILE '/var/lib/mysql-files/procedure_catalog.csv'
INTO TABLE procedure_catalog
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';
