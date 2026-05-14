-- ============================================================
-- Ygeiopolis General Hospital - Database Schema
-- install.sql
-- ============================================================
USE ygeiopolis;

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- ============================================================
-- DROP TABLES (reverse dependency order)
-- ============================================================
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS entity_image;
DROP TABLE IF EXISTS patient_review_doctor;
DROP TABLE IF EXISTS patient_review_hospitalization;
DROP TABLE IF EXISTS patient_allergy;
DROP TABLE IF EXISTS prescription;
DROP TABLE IF EXISTS active_substance;
DROP TABLE IF EXISTS drug_active_substance;
DROP TABLE IF EXISTS drug;
DROP TABLE IF EXISTS procedure_staff;
DROP TABLE IF EXISTS medical_procedure;
DROP TABLE IF EXISTS operating_room;
DROP TABLE IF EXISTS lab_test;
DROP TABLE IF EXISTS hospitalization;
DROP TABLE IF EXISTS triage;
DROP TABLE IF EXISTS ken_code;
DROP TABLE IF EXISTS icd10_code;
DROP TABLE IF EXISTS shift_assignment;
DROP TABLE IF EXISTS shift;
DROP TABLE IF EXISTS bed;
DROP TABLE IF EXISTS doctor_department;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS admin_staff;
DROP TABLE IF EXISTS nurse;
DROP TABLE IF EXISTS doctor;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS patient;

-- ============================================================
-- REFERENCE DATA TABLES
-- ============================================================

CREATE TABLE icd10_code (
    code        VARCHAR(10)  NOT NULL,
    description VARCHAR(255) NOT NULL,
    category    VARCHAR(10)  NOT NULL,  -- e.g. 'A00', 'I21'
    CONSTRAINT pk_icd10 PRIMARY KEY (code)
);

CREATE INDEX idx_icd10_category ON icd10_code (category);

-- ---------------------------------------------------------------
-- KEN (DRG) codes — Κλειστά Ενοποιημένα Νοσήλια
-- ---------------------------------------------------------------
CREATE TABLE ken_code (
    code            VARCHAR(10)    NOT NULL,
    description     VARCHAR(255)   NOT NULL,
    base_cost       DECIMAL(10,2)  NOT NULL CHECK (base_cost >= 0),
    mean_los_days   DECIMAL(6,2)   NOT NULL CHECK (mean_los_days > 0),  -- Mean Length of Stay
    daily_surcharge DECIMAL(10,2)  NOT NULL CHECK (daily_surcharge >= 0),
    CONSTRAINT pk_ken PRIMARY KEY (code)
);

-- ---------------------------------------------------------------
-- EMA Article 57 drugs
-- ---------------------------------------------------------------
CREATE TABLE drug (
    id              INT            NOT NULL AUTO_INCREMENT,
    product_name    VARCHAR(255)   NOT NULL,
    ema_product_no  VARCHAR(100),
    authorisation_no VARCHAR(100),
    authorisation_status VARCHAR(50),
    CONSTRAINT pk_drug PRIMARY KEY (id),
    CONSTRAINT uq_drug_ema UNIQUE (ema_product_no)
);

CREATE INDEX idx_drug_name ON drug (product_name);

CREATE TABLE active_substance (
    id      INT          NOT NULL AUTO_INCREMENT,
    name    VARCHAR(255) NOT NULL,
    CONSTRAINT pk_active_substance PRIMARY KEY (id),
    CONSTRAINT uq_active_substance_name UNIQUE (name)
);

CREATE INDEX idx_substance_name ON active_substance (name);

CREATE TABLE drug_active_substance (
    drug_id      INT NOT NULL,
    substance_id INT NOT NULL,
    CONSTRAINT pk_drug_substance PRIMARY KEY (drug_id, substance_id),
    CONSTRAINT fk_das_drug      FOREIGN KEY (drug_id)      REFERENCES drug (id)             ON DELETE CASCADE,
    CONSTRAINT fk_das_substance FOREIGN KEY (substance_id) REFERENCES active_substance (id) ON DELETE CASCADE
);

-- ============================================================
-- PATIENT
-- ============================================================
CREATE TABLE patient (
    amka            CHAR(11)      NOT NULL,
    first_name      VARCHAR(100)  NOT NULL,
    last_name       VARCHAR(100)  NOT NULL,
    fathers_name    VARCHAR(100)  NOT NULL,
    birth_date      DATE          NOT NULL,
    gender          CHAR(1)       NOT NULL CHECK (gender IN ('M', 'F', 'O')),
    weight_kg       DECIMAL(5,2)  CHECK (weight_kg > 0),
    height_cm       DECIMAL(5,1)  CHECK (height_cm > 0),
    address         VARCHAR(255),
    phone           VARCHAR(20),
    email           VARCHAR(150),
    occupation      VARCHAR(100),
    nationality     VARCHAR(100),
    -- Emergency contact stored inline (simplified; can be extended to a separate table)
    emergency_name  VARCHAR(200),
    emergency_phone VARCHAR(20),
    emergency_rel   VARCHAR(100),  -- relationship
    insurance       VARCHAR(100)  NOT NULL CHECK (insurance IN ('EFKA', 'Private', 'Uninsured', 'Other')),
    CONSTRAINT pk_patient PRIMARY KEY (amka)
);

CREATE INDEX idx_patient_name ON patient (last_name, first_name);
CREATE INDEX idx_patient_insurance ON patient (insurance);

CREATE TABLE patient_allergy (
    patient_amka VARCHAR(11) NOT NULL,
    substance_id INT         NOT NULL,
    notes        VARCHAR(255),
    CONSTRAINT pk_allergy PRIMARY KEY (patient_amka, substance_id),
    CONSTRAINT fk_allergy_patient   FOREIGN KEY (patient_amka) REFERENCES patient (amka)            ON DELETE CASCADE,
    CONSTRAINT fk_allergy_substance FOREIGN KEY (substance_id) REFERENCES active_substance (id)     ON DELETE CASCADE
);

CREATE INDEX idx_allergy_substance ON patient_allergy (substance_id);

-- ============================================================
-- STAFF (base table)
-- ============================================================
CREATE TABLE staff (
    amka        CHAR(11)     NOT NULL,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    birth_date  DATE         NOT NULL,
    email       VARCHAR(150),
    phone       VARCHAR(20),
    hire_date   DATE         NOT NULL,
    staff_type  VARCHAR(20)  NOT NULL CHECK (staff_type IN ('doctor', 'nurse', 'admin')),
    CONSTRAINT pk_staff PRIMARY KEY (amka)
);

CREATE INDEX idx_staff_type ON staff (staff_type);
CREATE INDEX idx_staff_name ON staff (last_name, first_name);

-- ============================================================
-- DEPARTMENT (forward declaration needed for FK from doctor)
-- ============================================================
CREATE TABLE department (
    id              INT          NOT NULL AUTO_INCREMENT,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    bed_count       INT          NOT NULL CHECK (bed_count >= 0),
    floor_building  VARCHAR(50),
    director_amka   CHAR(11),    -- FK to doctor; set after doctor table
    CONSTRAINT pk_department PRIMARY KEY (id),
    CONSTRAINT uq_department_name UNIQUE (name)
);

-- ============================================================
-- DOCTOR
-- ============================================================
CREATE TABLE doctor (
    amka            CHAR(11)     NOT NULL,
    license_no      VARCHAR(50)  NOT NULL,
    specialty       VARCHAR(100) NOT NULL,
    rank            VARCHAR(30)  NOT NULL CHECK (rank IN ('Resident', 'Registrar_B', 'Registrar_A', 'Director')),
    supervisor_amka CHAR(11)     DEFAULT NULL,
    CONSTRAINT pk_doctor            PRIMARY KEY (amka),
    CONSTRAINT fk_doctor_staff      FOREIGN KEY (amka)            REFERENCES staff (amka)  ON DELETE CASCADE,
    CONSTRAINT fk_doctor_supervisor FOREIGN KEY (supervisor_amka) REFERENCES doctor (amka) ON DELETE SET NULL,
    CONSTRAINT uq_doctor_license    UNIQUE (license_no)
);
-- Residents must have a supervisor; Directors must NOT
-- (enforced via triggers below)

CREATE INDEX idx_doctor_specialty  ON doctor (specialty);
CREATE INDEX idx_doctor_rank       ON doctor (rank);
CREATE INDEX idx_doctor_supervisor ON doctor (supervisor_amka);

-- Now add FK from department to doctor
ALTER TABLE department
    ADD CONSTRAINT fk_dept_director FOREIGN KEY (director_amka) REFERENCES doctor (amka) ON DELETE SET NULL;

-- Doctor ↔ Department (many-to-many)
CREATE TABLE doctor_department (
    doctor_amka   CHAR(11) NOT NULL,
    department_id INT      NOT NULL,
    CONSTRAINT pk_doctor_dept    PRIMARY KEY (doctor_amka, department_id),
    CONSTRAINT fk_dd_doctor      FOREIGN KEY (doctor_amka)   REFERENCES doctor     (amka) ON DELETE CASCADE,
    CONSTRAINT fk_dd_department  FOREIGN KEY (department_id) REFERENCES department (id)   ON DELETE CASCADE
);

-- ============================================================
-- NURSE
-- ============================================================
CREATE TABLE nurse (
    amka          CHAR(11)    NOT NULL,
    rank          VARCHAR(30) NOT NULL CHECK (rank IN ('Assistant', 'Nurse', 'Head_Nurse')),
    department_id INT         NOT NULL,
    CONSTRAINT pk_nurse           PRIMARY KEY (amka),
    CONSTRAINT fk_nurse_staff     FOREIGN KEY (amka)          REFERENCES staff      (amka) ON DELETE CASCADE,
    CONSTRAINT fk_nurse_dept      FOREIGN KEY (department_id) REFERENCES department (id)   ON DELETE RESTRICT
);

CREATE INDEX idx_nurse_dept ON nurse (department_id);
CREATE INDEX idx_nurse_rank ON nurse (rank);

-- ============================================================
-- ADMIN STAFF
-- ============================================================
CREATE TABLE admin_staff (
    amka          CHAR(11)     NOT NULL,
    role          VARCHAR(100) NOT NULL,   -- e.g. Secretary, Accountant
    office        VARCHAR(50),
    department_id INT          NOT NULL,
    CONSTRAINT pk_admin       PRIMARY KEY (amka),
    CONSTRAINT fk_admin_staff FOREIGN KEY (amka)          REFERENCES staff      (amka) ON DELETE CASCADE,
    CONSTRAINT fk_admin_dept  FOREIGN KEY (department_id) REFERENCES department (id)   ON DELETE RESTRICT
);

CREATE INDEX idx_admin_dept ON admin_staff (department_id);
CREATE INDEX idx_admin_role ON admin_staff (role);

-- ============================================================
-- BED
-- ============================================================
CREATE TABLE bed (
    id            INT         NOT NULL AUTO_INCREMENT,
    bed_number    VARCHAR(20) NOT NULL,
    department_id INT         NOT NULL,
    bed_type      VARCHAR(30) NOT NULL CHECK (bed_type IN ('ICU', 'Single', 'Multi', 'Other')),
    status        VARCHAR(20) NOT NULL DEFAULT 'Available'
                              CHECK (status IN ('Available', 'Occupied', 'Maintenance')),
    CONSTRAINT pk_bed           PRIMARY KEY (id),
    CONSTRAINT uq_bed_no_dept   UNIQUE (bed_number, department_id),
    CONSTRAINT fk_bed_dept      FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE CASCADE
);

CREATE INDEX idx_bed_dept   ON bed (department_id);
CREATE INDEX idx_bed_status ON bed (status);

-- ============================================================
-- SHIFT
-- ============================================================
CREATE TABLE shift (
    id            INT        NOT NULL AUTO_INCREMENT,
    department_id INT        NOT NULL,
    shift_date    DATE       NOT NULL,
    shift_type    VARCHAR(15) NOT NULL CHECK (shift_type IN ('Morning', 'Afternoon', 'Night')),
    CONSTRAINT pk_shift       PRIMARY KEY (id),
    CONSTRAINT uq_shift       UNIQUE (department_id, shift_date, shift_type),
    CONSTRAINT fk_shift_dept  FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE CASCADE
);

CREATE INDEX idx_shift_date ON shift (shift_date);
CREATE INDEX idx_shift_dept ON shift (department_id);

-- Shift assignments
CREATE TABLE shift_assignment (
    id         INT        NOT NULL AUTO_INCREMENT,
    shift_id   INT        NOT NULL,
    staff_amka CHAR(11)   NOT NULL,
    CONSTRAINT pk_shift_assignment   PRIMARY KEY (id),
    CONSTRAINT uq_shift_staff        UNIQUE (shift_id, staff_amka),
    CONSTRAINT fk_sa_shift           FOREIGN KEY (shift_id)   REFERENCES shift (id)  ON DELETE CASCADE,
    CONSTRAINT fk_sa_staff           FOREIGN KEY (staff_amka) REFERENCES staff (amka) ON DELETE CASCADE
);

CREATE INDEX idx_sa_staff    ON shift_assignment (staff_amka);
CREATE INDEX idx_sa_shift    ON shift_assignment (shift_id);

-- ============================================================
-- TRIAGE
-- ============================================================
CREATE TABLE triage (
    id              INT          NOT NULL AUTO_INCREMENT,
    patient_amka    CHAR(11)     NOT NULL,
    nurse_amka      CHAR(11)     NOT NULL,   -- triage nurse
    arrival_time    DATETIME     NOT NULL,
    symptoms        TEXT,
    urgency_level   TINYINT      NOT NULL CHECK (urgency_level BETWEEN 1 AND 5),
    -- outcome
    outcome         VARCHAR(20)  NOT NULL DEFAULT 'Discharged'
                                 CHECK (outcome IN ('Discharged', 'Admitted')),
    service_time    DATETIME,               -- when actually seen by doctor
    CONSTRAINT pk_triage        PRIMARY KEY (id),
    CONSTRAINT fk_triage_patient FOREIGN KEY (patient_amka) REFERENCES patient (amka) ON DELETE RESTRICT,
    CONSTRAINT fk_triage_nurse   FOREIGN KEY (nurse_amka)   REFERENCES nurse   (amka) ON DELETE RESTRICT
);

CREATE INDEX idx_triage_patient  ON triage (patient_amka);
CREATE INDEX idx_triage_urgency  ON triage (urgency_level);
CREATE INDEX idx_triage_arrival  ON triage (arrival_time);

-- ============================================================
-- HOSPITALIZATION
-- ============================================================
CREATE TABLE hospitalization (
    id                  INT           NOT NULL AUTO_INCREMENT,
    patient_amka        CHAR(11)      NOT NULL,
    bed_id              INT           NOT NULL,
    department_id       INT           NOT NULL,
    triage_id           INT           DEFAULT NULL,  -- NULL if not via ER
    admission_date      DATE          NOT NULL,
    discharge_date      DATE          DEFAULT NULL,
    admission_icd10     VARCHAR(10)   NOT NULL,
    discharge_icd10     VARCHAR(10)   DEFAULT NULL,
    ken_code            VARCHAR(10)   NOT NULL,
    base_cost           DECIMAL(10,2) NOT NULL CHECK (base_cost >= 0),
    surcharge           DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (surcharge >= 0),
    total_cost          DECIMAL(10,2) GENERATED ALWAYS AS (base_cost + surcharge) STORED,
    CONSTRAINT pk_hospitalization     PRIMARY KEY (id),
    CONSTRAINT fk_hosp_patient        FOREIGN KEY (patient_amka)    REFERENCES patient      (amka) ON DELETE RESTRICT,
    CONSTRAINT fk_hosp_bed            FOREIGN KEY (bed_id)          REFERENCES bed          (id)   ON DELETE RESTRICT,
    CONSTRAINT fk_hosp_dept           FOREIGN KEY (department_id)   REFERENCES department   (id)   ON DELETE RESTRICT,
    CONSTRAINT fk_hosp_triage         FOREIGN KEY (triage_id)       REFERENCES triage       (id)   ON DELETE SET NULL,
    CONSTRAINT fk_hosp_admission_icd  FOREIGN KEY (admission_icd10) REFERENCES icd10_code   (code) ON DELETE RESTRICT,
    CONSTRAINT fk_hosp_discharge_icd  FOREIGN KEY (discharge_icd10) REFERENCES icd10_code   (code) ON DELETE RESTRICT,
    CONSTRAINT fk_hosp_ken            FOREIGN KEY (ken_code)        REFERENCES ken_code     (code) ON DELETE RESTRICT,
    CONSTRAINT chk_hosp_dates         CHECK (discharge_date IS NULL OR discharge_date >= admission_date)
);

CREATE INDEX idx_hosp_patient    ON hospitalization (patient_amka);
CREATE INDEX idx_hosp_dept       ON hospitalization (department_id);
CREATE INDEX idx_hosp_admission  ON hospitalization (admission_date);
CREATE INDEX idx_hosp_discharge  ON hospitalization (discharge_date);
CREATE INDEX idx_hosp_icd        ON hospitalization (admission_icd10);
CREATE INDEX idx_hosp_ken        ON hospitalization (ken_code);

-- ============================================================
-- LAB TEST
-- ============================================================
CREATE TABLE lab_test (
    id                  INT           NOT NULL AUTO_INCREMENT,
    hospitalization_id  INT           NOT NULL,
    ordering_doctor_amka CHAR(11)     NOT NULL,
    code                VARCHAR(50)   NOT NULL,
    test_type           VARCHAR(100)  NOT NULL,  -- e.g. Haematological, Biochemical, Imaging
    test_date           DATE          NOT NULL,
    result_text         TEXT,
    result_value        DECIMAL(12,4),
    result_unit         VARCHAR(50),
    cost                DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
    CONSTRAINT pk_lab_test      PRIMARY KEY (id),
    CONSTRAINT fk_lt_hosp       FOREIGN KEY (hospitalization_id)   REFERENCES hospitalization (id)   ON DELETE CASCADE,
    CONSTRAINT fk_lt_doctor     FOREIGN KEY (ordering_doctor_amka) REFERENCES doctor          (amka) ON DELETE RESTRICT
);

CREATE INDEX idx_lt_hosp   ON lab_test (hospitalization_id);
CREATE INDEX idx_lt_doctor ON lab_test (ordering_doctor_amka);
CREATE INDEX idx_lt_date   ON lab_test (test_date);

-- ============================================================
-- OPERATING ROOM / PROCEDURE ROOM
-- ============================================================
CREATE TABLE operating_room (
    id          INT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    room_type   VARCHAR(30)  NOT NULL CHECK (room_type IN ('OR', 'Procedure_Room')),
    department_id INT        DEFAULT NULL,
    CONSTRAINT pk_or          PRIMARY KEY (id),
    CONSTRAINT uq_or_name     UNIQUE (name),
    CONSTRAINT fk_or_dept     FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE SET NULL
);

-- ============================================================
-- MEDICAL PROCEDURE
-- ============================================================
CREATE TABLE medical_procedure (
    id                  INT           NOT NULL AUTO_INCREMENT,
    hospitalization_id  INT           NOT NULL,
    code                VARCHAR(50)   NOT NULL,
    name                VARCHAR(255)  NOT NULL,
    category            VARCHAR(30)   NOT NULL CHECK (category IN ('Surgical', 'Diagnostic', 'Therapeutic')),
    start_datetime      DATETIME      NOT NULL,
    duration_minutes    INT           NOT NULL CHECK (duration_minutes > 0),
    cost                DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
    operating_room_id   INT           NOT NULL,
    primary_surgeon_amka CHAR(11)     NOT NULL,
    CONSTRAINT pk_procedure       PRIMARY KEY (id),
    CONSTRAINT fk_proc_hosp       FOREIGN KEY (hospitalization_id)  REFERENCES hospitalization (id)   ON DELETE CASCADE,
    CONSTRAINT fk_proc_room       FOREIGN KEY (operating_room_id)   REFERENCES operating_room  (id)   ON DELETE RESTRICT,
    CONSTRAINT fk_proc_surgeon    FOREIGN KEY (primary_surgeon_amka) REFERENCES doctor          (amka) ON DELETE RESTRICT
);

CREATE INDEX idx_proc_hosp     ON medical_procedure (hospitalization_id);
CREATE INDEX idx_proc_surgeon  ON medical_procedure (primary_surgeon_amka);
CREATE INDEX idx_proc_room     ON medical_procedure (operating_room_id);
CREATE INDEX idx_proc_start    ON medical_procedure (start_datetime);
CREATE INDEX idx_proc_category ON medical_procedure (category);

-- Procedure assistants (doctors or nurses)
CREATE TABLE procedure_staff (
    procedure_id INT        NOT NULL,
    staff_amka   CHAR(11)   NOT NULL,
    role         VARCHAR(50) NOT NULL DEFAULT 'Assistant',
    CONSTRAINT pk_proc_staff  PRIMARY KEY (procedure_id, staff_amka),
    CONSTRAINT fk_ps_proc     FOREIGN KEY (procedure_id) REFERENCES medical_procedure (id)   ON DELETE CASCADE,
    CONSTRAINT fk_ps_staff    FOREIGN KEY (staff_amka)   REFERENCES staff             (amka) ON DELETE CASCADE
);

-- ============================================================
-- PRESCRIPTION
-- ============================================================
CREATE TABLE prescription (
    id                  INT          NOT NULL AUTO_INCREMENT,
    hospitalization_id  INT          NOT NULL,
    doctor_amka         CHAR(11)     NOT NULL,
    patient_amka        CHAR(11)     NOT NULL,
    drug_id             INT          NOT NULL,
    start_date          DATE         NOT NULL,
    end_date            DATE,
    dosage              VARCHAR(100) NOT NULL,
    frequency           VARCHAR(100) NOT NULL,
    CONSTRAINT pk_prescription        PRIMARY KEY (id),
    CONSTRAINT uq_prescription        UNIQUE (doctor_amka, patient_amka, drug_id, start_date),
    CONSTRAINT fk_presc_hosp          FOREIGN KEY (hospitalization_id) REFERENCES hospitalization (id)   ON DELETE CASCADE,
    CONSTRAINT fk_presc_doctor        FOREIGN KEY (doctor_amka)        REFERENCES doctor          (amka) ON DELETE RESTRICT,
    CONSTRAINT fk_presc_patient       FOREIGN KEY (patient_amka)       REFERENCES patient         (amka) ON DELETE RESTRICT,
    CONSTRAINT fk_presc_drug          FOREIGN KEY (drug_id)            REFERENCES drug            (id)   ON DELETE RESTRICT,
    CONSTRAINT chk_presc_dates        CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_presc_hosp    ON prescription (hospitalization_id);
CREATE INDEX idx_presc_patient ON prescription (patient_amka);
CREATE INDEX idx_presc_doctor  ON prescription (doctor_amka);
CREATE INDEX idx_presc_drug    ON prescription (drug_id);

-- ============================================================
-- PATIENT REVIEWS
-- ============================================================

-- Review of the hospitalization itself (nursing care, cleanliness, food, overall)
CREATE TABLE patient_review_hospitalization (
    id                  INT       NOT NULL AUTO_INCREMENT,
    hospitalization_id  INT       NOT NULL,
    patient_amka        CHAR(11)  NOT NULL,
    nursing_care        TINYINT   NOT NULL CHECK (nursing_care BETWEEN 1 AND 5),
    cleanliness         TINYINT   NOT NULL CHECK (cleanliness  BETWEEN 1 AND 5),
    food                TINYINT   NOT NULL CHECK (food         BETWEEN 1 AND 5),
    overall_experience  TINYINT   NOT NULL CHECK (overall_experience BETWEEN 1 AND 5),
    review_date         DATE      NOT NULL,
    CONSTRAINT pk_rev_hosp       PRIMARY KEY (id),
    CONSTRAINT uq_rev_hosp       UNIQUE (hospitalization_id, patient_amka),
    CONSTRAINT fk_rh_hosp        FOREIGN KEY (hospitalization_id) REFERENCES hospitalization (id)   ON DELETE CASCADE,
    CONSTRAINT fk_rh_patient     FOREIGN KEY (patient_amka)       REFERENCES patient         (amka) ON DELETE CASCADE
);

CREATE INDEX idx_rev_hosp_hosp    ON patient_review_hospitalization (hospitalization_id);
CREATE INDEX idx_rev_hosp_patient ON patient_review_hospitalization (patient_amka);

-- Review of a specific doctor during a hospitalization
CREATE TABLE patient_review_doctor (
    id                  INT       NOT NULL AUTO_INCREMENT,
    hospitalization_id  INT       NOT NULL,
    patient_amka        CHAR(11)  NOT NULL,
    doctor_amka         CHAR(11)  NOT NULL,
    medical_care        TINYINT   NOT NULL CHECK (medical_care BETWEEN 1 AND 5),
    review_date         DATE      NOT NULL,
    CONSTRAINT pk_rev_doctor     PRIMARY KEY (id),
    CONSTRAINT uq_rev_doctor     UNIQUE (hospitalization_id, patient_amka, doctor_amka),
    CONSTRAINT fk_rd_hosp        FOREIGN KEY (hospitalization_id) REFERENCES hospitalization (id)   ON DELETE CASCADE,
    CONSTRAINT fk_rd_patient     FOREIGN KEY (patient_amka)       REFERENCES patient         (amka) ON DELETE CASCADE,
    CONSTRAINT fk_rd_doctor      FOREIGN KEY (doctor_amka)        REFERENCES doctor          (amka) ON DELETE CASCADE
);

CREATE INDEX idx_rev_doctor_doctor ON patient_review_doctor (doctor_amka);
CREATE INDEX idx_rev_doctor_hosp   ON patient_review_doctor (hospitalization_id);

-- ============================================================
-- ENTITY IMAGES (generic; covers departments, doctors, equipment, etc.)
-- ============================================================
CREATE TABLE entity_image (
    id           INT          NOT NULL AUTO_INCREMENT,
    entity_type  VARCHAR(50)  NOT NULL,  -- 'doctor', 'department', 'bed', 'procedure', etc.
    entity_id    VARCHAR(50)  NOT NULL,  -- stores the PK of the referenced entity as string
    image_url    VARCHAR(500) NOT NULL,
    description  TEXT,
    uploaded_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_entity_image PRIMARY KEY (id)
);

CREATE INDEX idx_image_entity ON entity_image (entity_type, entity_id);

-- ============================================================
-- Re-enable foreign key checks
-- ============================================================
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER $$

-- -----------------------------------------------------------
-- T1: Resident must have a supervisor
-- -----------------------------------------------------------
CREATE TRIGGER trg_doctor_resident_supervisor_insert
BEFORE INSERT ON doctor
FOR EACH ROW
BEGIN
    IF NEW.rank = 'Resident' AND NEW.supervisor_amka IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Residents must have a supervisor.';
    END IF;
END$$

CREATE TRIGGER trg_doctor_resident_supervisor_update
BEFORE UPDATE ON doctor
FOR EACH ROW
BEGIN
    IF NEW.rank = 'Resident' AND NEW.supervisor_amka IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Residents must have a supervisor.';
    END IF;
    IF NEW.rank = 'Director' AND NEW.supervisor_amka IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Directors cannot have a supervisor.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T2: No circular supervision chain (depth-limited check)
-- -----------------------------------------------------------
CREATE TRIGGER trg_doctor_no_circular_supervision
BEFORE INSERT ON doctor
FOR EACH ROW
BEGIN
    DECLARE current_amka CHAR(11);
    DECLARE depth INT DEFAULT 0;

    SET current_amka = NEW.supervisor_amka;

    WHILE current_amka IS NOT NULL AND depth < 100 DO
        IF current_amka = NEW.amka THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Circular supervision chain detected.';
        END IF;
        SELECT supervisor_amka INTO current_amka FROM doctor WHERE amka = current_amka;
        SET depth = depth + 1;
    END WHILE;
END$$

-- -----------------------------------------------------------
-- T3: No two procedures simultaneously in the same room
-- -----------------------------------------------------------
CREATE TRIGGER trg_proc_room_conflict
BEFORE INSERT ON medical_procedure
FOR EACH ROW
BEGIN
    DECLARE conflict INT;
    SELECT COUNT(*) INTO conflict
    FROM medical_procedure
    WHERE operating_room_id = NEW.operating_room_id
      AND id != NEW.id
      AND NEW.start_datetime < ADDTIME(start_datetime, SEC_TO_TIME(duration_minutes * 60))
      AND start_datetime     < ADDTIME(NEW.start_datetime, SEC_TO_TIME(NEW.duration_minutes * 60));

    IF conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Operating room already in use during this time slot.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T4: Doctor cannot participate in two simultaneous procedures
-- -----------------------------------------------------------
CREATE TRIGGER trg_proc_doctor_conflict
BEFORE INSERT ON medical_procedure
FOR EACH ROW
BEGIN
    DECLARE conflict INT;
    -- Check as primary surgeon
    SELECT COUNT(*) INTO conflict
    FROM medical_procedure
    WHERE primary_surgeon_amka = NEW.primary_surgeon_amka
      AND id != NEW.id
      AND NEW.start_datetime < ADDTIME(start_datetime, SEC_TO_TIME(duration_minutes * 60))
      AND start_datetime     < ADDTIME(NEW.start_datetime, SEC_TO_TIME(NEW.duration_minutes * 60));

    IF conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Doctor is already performing another procedure at this time.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T5: Allergy check on prescription insert
-- -----------------------------------------------------------
CREATE TRIGGER trg_prescription_allergy_check
BEFORE INSERT ON prescription
FOR EACH ROW
BEGIN
    DECLARE allergy_conflict INT;
    SELECT COUNT(*) INTO allergy_conflict
    FROM drug_active_substance das
    JOIN patient_allergy pa ON pa.substance_id = das.substance_id
    WHERE das.drug_id     = NEW.drug_id
      AND pa.patient_amka = NEW.patient_amka;

    IF allergy_conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot prescribe: patient is allergic to an active substance in this drug.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T6: Monthly shift limit per staff category
-- -----------------------------------------------------------
CREATE TRIGGER trg_shift_monthly_limit
BEFORE INSERT ON shift_assignment
FOR EACH ROW
BEGIN
    DECLARE shift_month    INT;
    DECLARE shift_year     INT;
    DECLARE shift_count    INT;
    DECLARE staff_category VARCHAR(20);
    DECLARE max_shifts     INT;

    SELECT MONTH(shift_date), YEAR(shift_date)
    INTO shift_month, shift_year
    FROM shift WHERE id = NEW.shift_id;

    SELECT staff_type INTO staff_category FROM staff WHERE amka = NEW.staff_amka;

    SET max_shifts = CASE staff_category
        WHEN 'doctor' THEN 15
        WHEN 'nurse'  THEN 20
        WHEN 'admin'  THEN 25
        ELSE 999
    END;

    SELECT COUNT(*) INTO shift_count
    FROM shift_assignment sa
    JOIN shift s ON s.id = sa.shift_id
    WHERE sa.staff_amka   = NEW.staff_amka
      AND MONTH(s.shift_date) = shift_month
      AND YEAR(s.shift_date)  = shift_year;

    IF shift_count >= max_shifts THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Monthly shift limit reached for this staff member.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T7: Minimum 8-hour rest between consecutive shifts
-- -----------------------------------------------------------
CREATE TRIGGER trg_shift_rest_period
BEFORE INSERT ON shift_assignment
FOR EACH ROW
BEGIN
    DECLARE new_start   DATETIME;
    DECLARE new_end     DATETIME;
    DECLARE prev_end    DATETIME;
    DECLARE next_start  DATETIME;
    DECLARE new_type    VARCHAR(15);
    DECLARE new_date    DATE;

    SELECT shift_date, shift_type INTO new_date, new_type
    FROM shift WHERE id = NEW.shift_id;

    SET new_start = CASE new_type
        WHEN 'Morning'   THEN TIMESTAMP(new_date, '07:00:00')
        WHEN 'Afternoon' THEN TIMESTAMP(new_date, '15:00:00')
        WHEN 'Night'     THEN TIMESTAMP(new_date, '23:00:00')
    END;
    SET new_end = CASE new_type
        WHEN 'Morning'   THEN TIMESTAMP(new_date, '15:00:00')
        WHEN 'Afternoon' THEN TIMESTAMP(new_date, '23:00:00')
        WHEN 'Night'     THEN TIMESTAMP(DATE_ADD(new_date, INTERVAL 1 DAY), '07:00:00')
    END;

    -- Check previous shift ends at least 8h before new shift starts
    SELECT MAX(
        CASE s.shift_type
            WHEN 'Morning'   THEN TIMESTAMP(s.shift_date, '15:00:00')
            WHEN 'Afternoon' THEN TIMESTAMP(s.shift_date, '23:00:00')
            WHEN 'Night'     THEN TIMESTAMP(DATE_ADD(s.shift_date, INTERVAL 1 DAY), '07:00:00')
        END
    ) INTO prev_end
    FROM shift_assignment sa
    JOIN shift s ON s.id = sa.shift_id
    WHERE sa.staff_amka = NEW.staff_amka
      AND (
          CASE s.shift_type
              WHEN 'Morning'   THEN TIMESTAMP(s.shift_date, '15:00:00')
              WHEN 'Afternoon' THEN TIMESTAMP(s.shift_date, '23:00:00')
              WHEN 'Night'     THEN TIMESTAMP(DATE_ADD(s.shift_date, INTERVAL 1 DAY), '07:00:00')
          END
      ) <= new_start;

    IF prev_end IS NOT NULL AND TIMESTAMPDIFF(HOUR, prev_end, new_start) < 8 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Minimum 8-hour rest period between shifts not met.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T8: Max 3 consecutive night shifts
-- -----------------------------------------------------------
CREATE TRIGGER trg_max_consecutive_nights
BEFORE INSERT ON shift_assignment
FOR EACH ROW
BEGIN
    DECLARE new_type  VARCHAR(15);
    DECLARE new_date  DATE;
    DECLARE night_count INT DEFAULT 0;

    SELECT shift_date, shift_type INTO new_date, new_type
    FROM shift WHERE id = NEW.shift_id;

    IF new_type = 'Night' THEN
        -- Count consecutive nights immediately preceding this one
        SELECT COUNT(*) INTO night_count
        FROM shift_assignment sa
        JOIN shift s ON s.id = sa.shift_id
        WHERE sa.staff_amka  = NEW.staff_amka
          AND s.shift_type   = 'Night'
          AND s.shift_date   IN (
              DATE_SUB(new_date, INTERVAL 1 DAY),
              DATE_SUB(new_date, INTERVAL 2 DAY),
              DATE_SUB(new_date, INTERVAL 3 DAY)
          );

        IF night_count >= 3 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Maximum of 3 consecutive night shifts exceeded.';
        END IF;
    END IF;
END$$

-- -----------------------------------------------------------
-- T9: Patient review only allowed after hospitalization is complete
-- -----------------------------------------------------------
CREATE TRIGGER trg_review_hosp_complete
BEFORE INSERT ON patient_review_hospitalization
FOR EACH ROW
BEGIN
    DECLARE disch DATE;
    SELECT discharge_date INTO disch
    FROM hospitalization WHERE id = NEW.hospitalization_id;

    IF disch IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot review: hospitalization is not yet complete.';
    END IF;
END$$

CREATE TRIGGER trg_review_doctor_complete
BEFORE INSERT ON patient_review_doctor
FOR EACH ROW
BEGIN
    DECLARE disch DATE;
    SELECT discharge_date INTO disch
    FROM hospitalization WHERE id = NEW.hospitalization_id;

    IF disch IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot review: hospitalization is not yet complete.';
    END IF;
END$$

-- -----------------------------------------------------------
-- T10: Doctor review only allowed if doctor prescribed during that hospitalization
-- -----------------------------------------------------------
CREATE TRIGGER trg_review_doctor_prescribed
BEFORE INSERT ON patient_review_doctor
FOR EACH ROW
BEGIN
    DECLARE presc_count INT;
    SELECT COUNT(*) INTO presc_count
    FROM prescription
    WHERE hospitalization_id = NEW.hospitalization_id
      AND doctor_amka        = NEW.doctor_amka
      AND patient_amka       = NEW.patient_amka;

    IF presc_count = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot review: doctor did not prescribe to this patient during this hospitalization.';
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- END OF install.sql
-- ============================================================
