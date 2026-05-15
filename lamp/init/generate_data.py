#!/usr/bin/env python3
"""
Ygeiopolis Hospital - Synthetic Data Generator
Generates load.sql with all synthetic hospital data.

The following tables are NOT populated here — load their official files first:
    - icd10_code       (from MoH file, fdl=3091)
    - ken_code         (from MoH file, fdl=3092)
    - procedure_catalog (from MoH file, fdl=1930)
    - drug             (from EMA Article 57 xlsx)
    - active_substance (from EMA Article 57 xlsx)
    - drug_active_substance (from EMA Article 57 xlsx)

Requirements:
    pip install faker

Usage:
    python generate_data.py  (writes load.sql to current directory)

IMPORTANT: Before running, set the constants in the CONFIG section below
to match the actual row counts in your loaded reference tables.

Counts generated:
    - 15 departments
    - 80 doctors
    - 120 nurses
    - 60 admin staff
    - 200 patients
    - 500 hospitalizations
    - 300 prescriptions
    - 200 lab tests
    - 150 medical procedures
    - 10 operating rooms
    - shifts covering 3 months
"""

import random
import sys
from datetime import date, datetime, timedelta
from faker import Faker

fake    = Faker('el_GR')   # Greek locale for realistic names
fake_en = Faker('en_US')

random.seed(42)  # reproducible output

# ============================================================
# CONFIG — adjust these to match your loaded reference data
# ============================================================

# Total number of drug rows loaded from EMA file
EMA_DRUG_COUNT = 1000

# Total number of active_substance rows loaded from EMA file
EMA_SUBSTANCE_COUNT = 500

# ICD-10 codes that exist in your loaded icd10_code table
# These must exactly match codes in the file you loaded.
# Add/remove as needed — these are the codes used as FKs.
ICD10_CODES = [
    "I21.0", "I21.1", "I50.0", "I10",   "J18.9",
    "J06.9", "K35.8", "K80.0", "N20.0", "S72.0",
    "C18.9", "E11.9", "J44.1", "G35",   "M54.5",
    "A09",   "F32.1", "N39.0", "K57.3", "I63.9",
]

# KEN codes that exist in your loaded ken_code table.
# Tuple: (code, base_cost, mean_los_days)
# base_cost and mean_los_days are used locally to compute surcharge — not inserted.
KEN_CODES = [
    ("112",  8500.00, 7.5),
    ("127",  3200.00, 5.8),
    ("143",  1800.00, 4.2),
    ("175",  4100.00, 6.0),
    ("179",  2200.00, 5.5),
    ("190",  2400.00, 5.0),
    ("202",  1600.00, 3.8),
    ("239",  3800.00, 7.0),
    ("243",  1400.00, 3.5),
    ("254",  6200.00, 8.5),
    ("290",  2100.00, 5.2),
    ("311",  2800.00, 3.0),
    ("320",  1700.00, 4.0),
    ("359",  4500.00, 3.5),
    ("371",  3100.00, 5.5),
    ("383",  1500.00, 3.2),
    ("394",  1900.00, 4.1),
    ("410",  2600.00, 2.0),
    ("430",  3400.00, 12.0),
    ("468",  9000.00, 9.0),
]

# Procedure catalog codes that exist in your loaded procedure_catalog table.
# These are the MoH codes from the file you loaded (categories A-E).
PROCEDURE_CATALOG_CODES = [
    "A01.01", "A01.02", "A02.01", "A02.02", "A02.03",
    "A02.04", "A03.01", "A03.02", "A03.03", "A04.01",
    "A04.02", "A05.01", "A05.02", "B01.01", "B01.02",
    "B02.01", "B02.02", "B02.03", "B03.01", "B03.02",
    "C01.01", "C01.02", "C02.01", "C02.02", "C03.01",
]

# ============================================================
# HELPERS
# ============================================================

output_lines = []

def emit(line=""):
    output_lines.append(line)

def sql_str(val):
    if val is None:
        return "NULL"
    val = str(val).replace("'", "''")
    return f"'{val}'"

def sql_date(d):
    if d is None:
        return "NULL"
    return f"'{d.strftime('%Y-%m-%d')}'"

def sql_datetime(dt):
    if dt is None:
        return "NULL"
    return f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'"

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def random_amka():
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])

# ============================================================
# DOMAIN CONSTANTS (not inserted — used only for FK references)
# ============================================================

# Specialties
SPECIALTIES = [
    "Cardiology", "Surgery", "Internal Medicine", "Orthopedics",
    "Neurology", "Oncology", "Pulmonology", "Gastroenterology",
    "Nephrology", "Urology", "Gynecology", "Pediatrics",
    "Psychiatry", "Radiology", "Anesthesiology",
]

# Department names
DEPT_NAMES = [
    ("Cardiology",          "Καρδιολογική Κλινική"),
    ("Surgery",             "Χειρουργική Κλινική"),
    ("Internal Medicine",   "Παθολογική Κλινική"),
    ("Orthopedics",         "Ορθοπεδική Κλινική"),
    ("Neurology",           "Νευρολογική Κλινική"),
    ("Oncology",            "Ογκολογική Κλινική"),
    ("Pulmonology",         "Πνευμονολογική Κλινική"),
    ("Gastroenterology",    "Γαστρεντερολογική Κλινική"),
    ("Nephrology",          "Νεφρολογική Κλινική"),
    ("Urology",             "Ουρολογική Κλινική"),
    ("Gynecology",          "Γυναικολογική Κλινική"),
    ("Pediatrics",          "Παιδιατρική Κλινική"),
    ("Psychiatry",          "Ψυχιατρική Κλινική"),
    ("ICU",                 "Μονάδα Εντατικής Θεραπείας"),
    ("Emergency",           "Τμήμα Επειγόντων Περιστατικών"),
]

# ============================================================
# MAIN GENERATION
# ============================================================

emit("-- ============================================================")
emit("-- Ygeiopolis Hospital - Synthetic Data")
emit("-- Generated by generate_data.py")
emit("-- ============================================================")
emit()
emit("SET FOREIGN_KEY_CHECKS = 0;")
emit("SET NAMES utf8mb4;")
emit()

# ============================================================
# 1. REFERENCE DATA
# ============================================================

# ============================================================
# 1. DEPARTMENTS (no director yet — set later)
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Departments")
emit("-- ------------------------------------------------------------")
dept_ids = {}  # name -> id (1-indexed)
for i, (specialty, greek_name) in enumerate(DEPT_NAMES, 1):
    dept_ids[specialty] = i
    bed_count = random.randint(15, 50)
    floor_building = f"Floor {random.randint(1, 6)}, Building {random.choice(['A','B','C'])}"
    emit(f"INSERT INTO department (id, name, description, bed_count, floor_building, director_amka) "
         f"VALUES ({i}, {sql_str(greek_name)}, {sql_str(f'{greek_name} - Γενικό Νοσοκομείο Υγειόπολης')}, "
         f"{bed_count}, {sql_str(floor_building)}, NULL);")
emit()

# ============================================================
# 3. STAFF + DOCTORS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Staff + Doctors")
emit("-- ------------------------------------------------------------")

# Track AMKAs
used_amkas = set()
def gen_amka():
    while True:
        a = random_amka()
        if a not in used_amkas:
            used_amkas.add(a)
            return a

doctors = []  # list of dicts

# We need at least one Director per specialty for supervision chain
# Strategy: generate doctors in order Directors -> Registrar_A -> Registrar_B -> Residents

ranks_distribution = [
    ("Director",    10),
    ("Registrar_A", 20),
    ("Registrar_B", 25),
    ("Resident",    25),
]

doctor_amkas_by_rank = {r: [] for r, _ in ranks_distribution}

total_doctors = 80
doc_count = 0

for rank, count in ranks_distribution:
    for _ in range(count):
        amka = gen_amka()
        first = fake.first_name()
        last  = fake.last_name()
        birth = random_date(date(1960, 1, 1), date(1995, 12, 31))
        # Young doctors constraint for Q5: ensure some are < 35
        if rank in ("Resident", "Registrar_B") and doc_count % 4 == 0:
            birth = random_date(date(1991, 1, 1), date(2000, 12, 31))
        hire  = random_date(date(2000, 1, 1), date(2023, 12, 31))
        email = f"{fake_en.user_name()}@ygeiopolis.gr"
        phone = fake.phone_number()[:20]
        specialty = random.choice(SPECIALTIES)
        license_no = f"ΙΑΤ{random.randint(100000, 999999)}"

        emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
             f"VALUES ({sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_date(birth)}, "
             f"{sql_str(email)}, {sql_str(phone)}, {sql_date(hire)}, 'doctor');")

        doctors.append({
            'amka': amka, 'first': first, 'last': last,
            'birth': birth, 'specialty': specialty, 'rank': rank,
            'license_no': license_no,
        })
        doctor_amkas_by_rank[rank].append(amka)
        doc_count += 1

emit()

# Insert doctor rows (without supervisors first)
emit("-- Doctor subclass rows (supervisors set in second pass)")
for d in doctors:
    emit(f"INSERT INTO doctor (amka, license_no, specialty, rank, supervisor_amka) "
         f"VALUES ({sql_str(d['amka'])}, {sql_str(d['license_no'])}, "
         f"{sql_str(d['specialty'])}, {sql_str(d['rank'])}, NULL);")
emit()

# Second pass: set supervisors
emit("-- Strong hierarchical supervision model")

for d in doctors:
    if d['rank'] == 'Resident':
        sup_pool = doctor_amkas_by_rank['Registrar_A']
        if not sup_pool:
            sup_pool = doctor_amkas_by_rank['Registrar_B']
        sup = random.choice(sup_pool)

    elif d['rank'] == 'Registrar_B':
        sup_pool = doctor_amkas_by_rank['Registrar_A'] + doctor_amkas_by_rank['Director']
        sup = random.choice(sup_pool)

    elif d['rank'] == 'Registrar_A':
        sup_pool = doctor_amkas_by_rank['Director']
        if sup_pool:
            sup = random.choice(sup_pool)
        else:
            continue

    else:
        continue  # Directors

    emit(
        f"UPDATE doctor SET supervisor_amka = {sql_str(sup)} "
        f"WHERE amka = {sql_str(d['amka'])};"
    )
emit()

# Doctor-Department assignments
emit("-- Doctor-Department assignments (doctors belong to 1-3 departments)")
for d in doctors:
    specialty_dept = None
    for s, _ in DEPT_NAMES:
        if s == d['specialty']:
            specialty_dept = dept_ids[s]
            break
    if specialty_dept is None:
        specialty_dept = random.randint(1, len(DEPT_NAMES))

    depts = {specialty_dept}
    extra = random.randint(0, 2)
    while len(depts) <= extra:
        depts.add(random.randint(1, len(DEPT_NAMES)))

    for dept_id in depts:
        emit(f"INSERT IGNORE INTO doctor_department (doctor_amka, department_id) "
             f"VALUES ({sql_str(d['amka'])}, {dept_id});")
emit()

# Set department directors (must be a Director-rank doctor)
emit("-- Set department directors")
director_amkas = doctor_amkas_by_rank['Director']
for i, (specialty, _) in enumerate(DEPT_NAMES):
    dir_amka = director_amkas[i % len(director_amkas)]
    emit(f"UPDATE department SET director_amka = {sql_str(dir_amka)} WHERE id = {dept_ids[specialty]};")
emit()

# ============================================================
# 4. NURSES
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Staff + Nurses")
emit("-- ------------------------------------------------------------")

nurses = []
nurse_ranks = ['Assistant', 'Nurse', 'Head_Nurse']

for i in range(120):
    amka = gen_amka()
    first = fake.first_name_female()
    last  = fake.last_name()
    birth = random_date(date(1970, 1, 1), date(2000, 12, 31))
    hire  = random_date(date(2005, 1, 1), date(2023, 12, 31))
    email = f"{fake_en.user_name()}@ygeiopolis.gr"
    phone = fake.phone_number()[:20]
    rank  = random.choices(nurse_ranks, weights=[30, 60, 10])[0]
    dept_id = random.randint(1, len(DEPT_NAMES))

    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_date(birth)}, "
         f"{sql_str(email)}, {sql_str(phone)}, {sql_date(hire)}, 'nurse');")
    emit(f"INSERT INTO nurse (amka, rank, department_id) "
         f"VALUES ({sql_str(amka)}, {sql_str(rank)}, {dept_id});")

    nurses.append({'amka': amka, 'rank': rank, 'dept_id': dept_id})
emit()

# ============================================================
# 5. ADMIN STAFF
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Staff + Admin")
emit("-- ------------------------------------------------------------")

admin_roles = ['Secretary', 'Accountant', 'Receptionist', 'HR Officer', 'IT Support', 'Logistics']
admins = []

for i in range(60):
    amka = gen_amka()
    first = fake.first_name()
    last  = fake.last_name()
    birth = random_date(date(1965, 1, 1), date(1998, 12, 31))
    hire  = random_date(date(2000, 1, 1), date(2023, 12, 31))
    email = f"{fake_en.user_name()}@ygeiopolis.gr"
    phone = fake.phone_number()[:20]
    role  = random.choice(admin_roles)
    office = f"Office {random.randint(100, 399)}"
    dept_id = random.randint(1, len(DEPT_NAMES))

    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_date(birth)}, "
         f"{sql_str(email)}, {sql_str(phone)}, {sql_date(hire)}, 'admin');")
    emit(f"INSERT INTO admin_staff (amka, role, office, department_id) "
         f"VALUES ({sql_str(amka)}, {sql_str(role)}, {sql_str(office)}, {dept_id});")

    admins.append({'amka': amka, 'role': role, 'dept_id': dept_id})
emit()

# ============================================================
# 6. BEDS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Beds")
emit("-- ------------------------------------------------------------")

bed_types = ['ICU', 'Single', 'Multi', 'Other']
bed_statuses = ['Available', 'Occupied', 'Maintenance']
beds = []  # list of (id, dept_id)
bed_id = 1

for dept_id in range(1, len(DEPT_NAMES) + 1):
    count = random.randint(10, 30)
    for j in range(1, count + 1):
        bed_number = f"{dept_id:02d}-{j:03d}"
        btype  = random.choices(bed_types, weights=[10, 20, 60, 10])[0]
        status = random.choices(bed_statuses, weights=[50, 40, 10])[0]
        emit(f"INSERT INTO bed (id, bed_number, department_id, bed_type, status) "
             f"VALUES ({bed_id}, {sql_str(bed_number)}, {dept_id}, {sql_str(btype)}, {sql_str(status)});")
        beds.append({'id': bed_id, 'dept_id': dept_id})
        bed_id += 1
emit()

# ============================================================
# 7. OPERATING ROOMS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Operating Rooms")
emit("-- ------------------------------------------------------------")

op_rooms = []
for i in range(1, 11):
    rtype = 'OR' if i <= 6 else 'Procedure_Room'
    name  = f"{'Χειρουργείο' if rtype == 'OR' else 'Αίθουσα Επεμβάσεων'} {i}"
    dept_id = random.randint(1, len(DEPT_NAMES))
    emit(f"INSERT INTO operating_room (id, name, room_type, department_id) "
         f"VALUES ({i}, {sql_str(name)}, {sql_str(rtype)}, {dept_id});")
    op_rooms.append(i)
emit()

# ============================================================
# 8. PATIENTS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Patients")
emit("-- ------------------------------------------------------------")

patients = []
insurance_types = ['EFKA', 'Private', 'Uninsured', 'Other']

for i in range(200):
    amka = gen_amka()
    first = fake.first_name()
    last  = fake.last_name()
    fathers = fake.first_name_male()
    birth = random_date(date(1940, 1, 1), date(2005, 12, 31))
    gender = random.choice(['M', 'F'])
    weight = round(random.uniform(50, 120), 1)
    height = round(random.uniform(155, 195), 1)
    address = fake.address().replace('\n', ', ')[:255]
    phone = fake.phone_number()[:20]
    email = f"{fake_en.user_name()}@gmail.com"
    occupation = random.choice(['Engineer', 'Teacher', 'Doctor', 'Lawyer', 'Retired', 'Student', 'Merchant'])
    nationality = random.choice(['Greek', 'Greek', 'Greek', 'Albanian', 'Bulgarian', 'Romanian', 'German'])
    insurance = random.choices(insurance_types, weights=[50, 30, 10, 10])[0]
    em_name  = fake.name()
    em_phone = fake.phone_number()[:20]
    em_rel   = random.choice(['Spouse', 'Parent', 'Child', 'Sibling', 'Friend'])

    emit(f"INSERT INTO patient (amka, first_name, last_name, fathers_name, birth_date, gender, "
         f"weight_kg, height_cm, address, phone, email, occupation, nationality, "
         f"emergency_name, emergency_phone, emergency_rel, insurance) VALUES ("
         f"{sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_str(fathers)}, "
         f"{sql_date(birth)}, {sql_str(gender)}, {weight}, {height}, "
         f"{sql_str(address)}, {sql_str(phone)}, {sql_str(email)}, "
         f"{sql_str(occupation)}, {sql_str(nationality)}, "
         f"{sql_str(em_name)}, {sql_str(em_phone)}, {sql_str(em_rel)}, "
         f"{sql_str(insurance)});")

    patients.append({'amka': amka, 'birth': birth})
emit()

# ============================================================
# 9. PATIENT ALLERGIES (subset of patients)
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Patient Allergies")
emit("-- ------------------------------------------------------------")
emit("-- Note: substance_ids 1-10 assumed loaded from EMA data")
emit("-- Adjust substance_id range to match your loaded active_substance table")

allergy_patients = random.sample(patients, 40)
for p in allergy_patients:
    num_allergies = random.randint(1, 3)
    substance_ids = random.sample(range(1, EMA_SUBSTANCE_COUNT + 1), num_allergies)
    for sid in substance_ids:
        emit(f"INSERT IGNORE INTO patient_allergy (patient_amka, substance_id) "
             f"VALUES ({sql_str(p['amka'])}, {sid});")
emit()

# ============================================================
# 10. SHIFTS (3 months: Jan-Mar 2025)
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Shifts (January - March 2025)")
emit("-- ------------------------------------------------------------")

shift_types = ['Morning', 'Afternoon', 'Night']
shift_start = date(2025, 1, 1)
shift_end   = date(2025, 3, 31)

shifts = []  # list of dicts
shift_id = 1

current = shift_start
while current <= shift_end:
    for dept_id in range(1, len(DEPT_NAMES) + 1):
        for stype in shift_types:
            emit(f"INSERT INTO shift (id, department_id, shift_date, shift_type) "
                 f"VALUES ({shift_id}, {dept_id}, {sql_date(current)}, {sql_str(stype)});")
            shifts.append({'id': shift_id, 'dept_id': dept_id, 'date': current, 'type': stype})
            shift_id += 1
    current += timedelta(days=1)
emit()

# ============================================================
# 11. SHIFT ASSIGNMENTS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Shift Assignments")
emit("-- Note: we bypass triggers here for bulk load; constraints")
emit("--       verified at application level per README assumptions")
emit("-- ------------------------------------------------------------")

# Track monthly shift counts per staff member to respect limits
monthly_counts = {}  # (amka, year, month) -> count

def can_assign(amka, shift_date, staff_type):
    key = (amka, shift_date.year, shift_date.month)
    count = monthly_counts.get(key, 0)
    limit = {'doctor': 15, 'nurse': 20, 'admin': 25}.get(staff_type, 999)
    return count < limit

def record_assign(amka, shift_date):
    key = (amka, shift_date.year, shift_date.month)
    monthly_counts[key] = monthly_counts.get(key, 0) + 1

sa_id = 1

# Group shifts by (dept, date, type)
for shift in shifts:
    dept_id = shift['dept_id']
    sdate   = shift['date']
    stype   = shift['type']
    sid     = shift['id']

    # Get doctors in this department
    dept_doctors = [d for d in doctors
                    if any(True for dd in doctors
                           if dd['amka'] == d['amka'])]
    # simplified: pick from all doctors, filter by dept via doctor_department
    # for generation purposes we assign from global pool
    available_docs = [d for d in doctors if can_assign(d['amka'], sdate, 'doctor')]
    available_nurses = [n for n in nurses if can_assign(n['amka'], sdate, 'nurse')]
    available_admins = [a for a in admins if can_assign(a['amka'], sdate, 'admin')]

    # Pick minimums: 3 doctors, 6 nurses, 2 admin
    chosen_docs   = random.sample(available_docs,   min(random.randint(3, 5), len(available_docs)))
    chosen_nurses = random.sample(available_nurses, min(random.randint(6, 9), len(available_nurses)))
    chosen_admins = random.sample(available_admins, min(random.randint(2, 3), len(available_admins)))

    # Ensure at least one Registrar_A or Director if any Resident assigned
    has_resident = any(d['rank'] == 'Resident' for d in chosen_docs)
    has_senior   = any(d['rank'] in ('Registrar_A', 'Director') for d in chosen_docs)
    if has_resident and not has_senior:
        seniors = [d for d in available_docs if d['rank'] in ('Registrar_A', 'Director')]
        if seniors:
            chosen_docs.append(random.choice(seniors))

    for d in chosen_docs:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(d['amka'])});")
        record_assign(d['amka'], sdate)
        sa_id += 1

    for n in chosen_nurses:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(n['amka'])});")
        record_assign(n['amka'], sdate)
        sa_id += 1

    for a in chosen_admins:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(a['amka'])});")
        record_assign(a['amka'], sdate)
        sa_id += 1

emit()

# ============================================================
# 12. TRIAGE
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Triage")
emit("-- ------------------------------------------------------------")

triage_records = []
er_dept_id = dept_ids.get('Emergency', 15)
er_nurses = [n for n in nurses if n['dept_id'] == er_dept_id] or nurses[:10]

triage_id = 1
# Generate 600 triage records (some lead to hospitalization, some don't)
triage_start = date(2023, 1, 1)
triage_end   = date(2024, 12, 31)

for i in range(600):
    patient = random.choice(patients)
    nurse   = random.choice(er_nurses)
    arrival = datetime.combine(
        random_date(triage_start, triage_end),
        datetime.min.time()
    ) + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
    urgency = random.choices([1,2,3,4,5], weights=[5, 15, 30, 30, 20])[0]
    wait_minutes = {1: 5, 2: 15, 3: 30, 4: 60, 5: 120}[urgency] + random.randint(0, 30)
    service_time = arrival + timedelta(minutes=wait_minutes)
    outcome = random.choices(['Admitted', 'Discharged'], weights=[40, 60])[0]

    emit(f"INSERT INTO triage (id, patient_amka, nurse_amka, arrival_time, symptoms, "
         f"urgency_level, outcome, service_time) VALUES ("
         f"{triage_id}, {sql_str(patient['amka'])}, {sql_str(nurse['amka'])}, "
         f"{sql_datetime(arrival)}, {sql_str('Symptoms recorded at triage')}, "
         f"{urgency}, {sql_str(outcome)}, {sql_datetime(service_time)});")

    triage_records.append({
        'id': triage_id, 'patient_amka': patient['amka'],
        'outcome': outcome, 'arrival': arrival
    })
    triage_id += 1
emit()

# ============================================================
# 13. HOSPITALIZATIONS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Hospitalizations")
emit("-- ------------------------------------------------------------")

hosp_records = []
hosp_id = 1

# Admitted triage records
admitted_triages = [t for t in triage_records if t['outcome'] == 'Admitted']

# We need 500 hospitalizations
# Use admitted triages for some, generate rest directly
hosp_start = date(2023, 1, 1)
hosp_end   = date(2024, 12, 31)

for i in range(500):
    # Pick patient — ensure some patients hospitalized 4+ times in same dept (for Q3)
    if i < 30 and i % 5 == 0:
        # Force repeat hospitalizations for same patient in same dept
        patient = patients[i // 5]
        dept_id = random.randint(1, 5)
    else:
        patient = random.choice(patients)
        dept_id = random.randint(1, len(DEPT_NAMES))

    # Find a bed in this department
    dept_beds = [b for b in beds if b['dept_id'] == dept_id]
    if not dept_beds:
        dept_beds = beds[:5]
    bed = random.choice(dept_beds)

    # Use triage if available
    triage_ref = None
    if i < len(admitted_triages):
        triage_ref = admitted_triages[i]['id']
        adm_date = admitted_triages[i]['arrival'].date()
        if adm_date < hosp_start:
            adm_date = hosp_start
    else:
        adm_date = random_date(hosp_start, hosp_end)

    # KEN code and costs
    ken = random.choice(KEN_CODES)
    ken_code_val = ken[0]
    base_cost    = ken[1]
    mean_los     = ken[2]
    # daily_surcharge = base_cost / mean_los_days (our assumption, see README)
    daily_surcharge = round(base_cost / mean_los, 2)

    # Actual length of stay
    actual_los = random.choices(
        range(1, 20),
        weights=[5,8,12,15,12,10,8,6,5,4,3,3,2,2,2,1,1,1,1]
    )[0]
    disc_date = adm_date + timedelta(days=actual_los)
    if disc_date > date(2025, 6, 30):
        disc_date = date(2025, 6, 30)

    # Surcharge: MAX(0, actual_days - mean_los) * daily_surcharge
    extra_days = max(0, actual_los - mean_los)
    surcharge  = round(extra_days * daily_surcharge, 2)

    adm_icd  = random.choice(ICD10_CODES)
    disc_icd = random.choice(ICD10_CODES)

    emit(f"INSERT INTO hospitalization (id, patient_amka, bed_id, department_id, triage_id, "
         f"admission_date, discharge_date, admission_icd10, discharge_icd10, "
         f"ken_code, base_cost, surcharge) VALUES ("
         f"{hosp_id}, {sql_str(patient['amka'])}, {bed['id']}, {dept_id}, "
         f"{'NULL' if triage_ref is None else triage_ref}, "
         f"{sql_date(adm_date)}, {sql_date(disc_date)}, "
         f"{sql_str(adm_icd)}, {sql_str(disc_icd)}, "
         f"{sql_str(ken_code_val)}, {base_cost}, {surcharge});")

    hosp_records.append({
        'id': hosp_id, 'patient_amka': patient['amka'],
        'dept_id': dept_id, 'adm_date': adm_date, 'disc_date': disc_date,
    })
    hosp_id += 1
emit()

# ============================================================
# 14. LAB TESTS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Lab Tests")
emit("-- ------------------------------------------------------------")

test_types = ['Haematological', 'Biochemical', 'Imaging', 'Microbiological', 'Pathological']
lt_id = 1

selected_hosps = random.sample(hosp_records, min(200, len(hosp_records)))
for h in selected_hosps:
    doc = random.choice(doctors)
    ttype = random.choice(test_types)
    tdate = h['adm_date'] + timedelta(days=random.randint(0, max(1, (h['disc_date'] - h['adm_date']).days)))
    result_val = round(random.uniform(0.1, 999.9), 2)
    units = random.choice(['mg/dL', 'mmol/L', 'U/L', 'g/L', '%', 'cells/μL'])
    cost  = round(random.uniform(20, 300), 2)
    code  = f"LAB{random.randint(1000,9999)}"

    emit(f"INSERT INTO lab_test (id, hospitalization_id, ordering_doctor_amka, code, test_type, "
         f"test_date, result_text, result_value, result_unit, cost) VALUES ("
         f"{lt_id}, {h['id']}, {sql_str(doc['amka'])}, {sql_str(code)}, {sql_str(ttype)}, "
         f"{sql_date(tdate)}, {sql_str('Result within normal range')}, "
         f"{result_val}, {sql_str(units)}, {cost});")
    lt_id += 1
emit()

# ============================================================
# 15. MEDICAL PROCEDURES
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Medical Procedures")
emit("-- ------------------------------------------------------------")

proc_id = 1
# Track room usage: room_id -> list of (start, end) datetimes
room_schedule = {r: [] for r in op_rooms}
# Track doctor schedule: amka -> list of (start, end)
doctor_schedule = {}

def is_room_free(room_id, start_dt, end_dt):
    for s, e in room_schedule[room_id]:
        if not (end_dt <= s or start_dt >= e):
            return False
    return True

def is_doctor_free(amka, start_dt, end_dt):
    for s, e in doctor_schedule.get(amka, []):
        if not (end_dt <= s or start_dt >= e):
            return False
    return True

selected_hosps_proc = random.sample(hosp_records, min(150, len(hosp_records)))

for h in selected_hosps_proc:
    catalog_item = random.choice(PROCEDURE_CATALOG_CODES)
    cat_code  = catalog_item
    duration  = random.randint(30, 240)
    cost      = round(random.uniform(500, 8000), 2)

    # Find a free room
    proc_date = h['adm_date'] + timedelta(days=random.randint(0, max(1, (h['disc_date'] - h['adm_date']).days)))
    hour      = random.randint(8, 16)
    start_dt  = datetime.combine(proc_date, datetime.min.time()) + timedelta(hours=hour)
    end_dt    = start_dt + timedelta(minutes=duration)

    room_id = None
    for r in random.sample(op_rooms, len(op_rooms)):
        if is_room_free(r, start_dt, end_dt):
            room_id = r
            break
    if room_id is None:
        continue  # skip if no room available

    # Find a free surgeon
    surgeon = None
    for d in random.sample(doctors, len(doctors)):
        if is_doctor_free(d['amka'], start_dt, end_dt):
            surgeon = d
            break
    if surgeon is None:
        continue

    room_schedule[room_id].append((start_dt, end_dt))
    if surgeon['amka'] not in doctor_schedule:
        doctor_schedule[surgeon['amka']] = []
    doctor_schedule[surgeon['amka']].append((start_dt, end_dt))

    emit(f"INSERT INTO medical_procedure (id, catalog_code, hospitalization_id, start_datetime, "
         f"duration_minutes, cost, operating_room_id, primary_surgeon_amka) VALUES ("
         f"{proc_id}, {sql_str(cat_code)}, {h['id']}, {sql_datetime(start_dt)}, "
         f"{duration}, {cost}, {room_id}, {sql_str(surgeon['amka'])});")

    # Add 1-2 assistants
    num_assistants = random.randint(1, 2)
    all_staff_amkas = [d['amka'] for d in doctors] + [n['amka'] for n in nurses]
    assistant_pool = [a for a in all_staff_amkas if a != surgeon['amka']]
    for asst_amka in random.sample(assistant_pool, min(num_assistants, len(assistant_pool))):
        emit(f"INSERT IGNORE INTO procedure_staff (procedure_id, staff_amka, role) "
             f"VALUES ({proc_id}, {sql_str(asst_amka)}, 'Assistant');")

    proc_id += 1
emit()

# ============================================================
# 16. PRESCRIPTIONS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Prescriptions")
emit("-- drug_ids reference the EMA drug table loaded from file")
emit("-- ------------------------------------------------------------")

dosage_options   = ['1 tablet', '2 tablets', '500mg', '250mg', '1g', '10mg', '20mg', '50mg']
frequency_options = ['Once daily', 'Twice daily', 'Three times daily', 'Every 8 hours', 'As needed']

presc_id = 1
presc_keys = set()  # (doctor, patient, drug, start_date)
presc_records = []  # track for review generation

selected_hosps_presc = random.sample(hosp_records, min(300, len(hosp_records)))

for h in selected_hosps_presc:
    doc   = random.choice(doctors)
    drug_id = random.randint(1, EMA_DRUG_COUNT)
    start = h['adm_date'] + timedelta(days=random.randint(0, 2))
    end   = start + timedelta(days=random.randint(3, 14))

    key = (doc['amka'], h['patient_amka'], drug_id, start)
    if key in presc_keys:
        continue
    presc_keys.add(key)

    dosage    = random.choice(dosage_options)
    frequency = random.choice(frequency_options)

    emit(f"INSERT INTO prescription (id, hospitalization_id, doctor_amka, patient_amka, drug_id, "
         f"start_date, end_date, dosage, frequency) VALUES ("
         f"{presc_id}, {h['id']}, {sql_str(doc['amka'])}, {sql_str(h['patient_amka'])}, "
         f"{drug_id}, {sql_date(start)}, {sql_date(end)}, "
         f"{sql_str(dosage)}, {sql_str(frequency)});")

    presc_records.append({
        'hospitalization_id': h['id'],
        'doctor_amka': doc['amka'],
        'patient_amka': h['patient_amka'],
    })
    presc_id += 1
emit()

# ============================================================
# 17. PATIENT REVIEWS
# ============================================================

emit("-- ------------------------------------------------------------")
emit("-- Patient Reviews")
emit("-- ------------------------------------------------------------")

rev_hosp_id  = 1
rev_doc_id   = 1

# Build a lookup: hospitalization_id -> list of doctor_amkas who prescribed
hosp_prescribers = {}
for p in presc_records:
    hid = p['hospitalization_id']
    if hid not in hosp_prescribers:
        hosp_prescribers[hid] = []
    if p['doctor_amka'] not in hosp_prescribers[hid]:
        hosp_prescribers[hid].append(p['doctor_amka'])

# Only completed hospitalizations (have discharge_date)
completed = [h for h in hosp_records if h['disc_date'] is not None]
review_sample = random.sample(completed, min(200, len(completed)))

for h in review_sample:
    review_date = h['disc_date'] + timedelta(days=random.randint(1, 30))

    # Hospitalization review
    emit(f"INSERT IGNORE INTO patient_review_hospitalization "
         f"(id, hospitalization_id, patient_amka, nursing_care, cleanliness, food, overall_experience, review_date) "
         f"VALUES ({rev_hosp_id}, {h['id']}, {sql_str(h['patient_amka'])}, "
         f"{random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, "
         f"{random.randint(1,5)}, {sql_date(review_date)});")
    rev_hosp_id += 1

    # Doctor review — only for doctors who actually prescribed in this hospitalization (T10)
    prescribers = hosp_prescribers.get(h['id'], [])
    if not prescribers:
        continue  # no prescriptions in this hospitalization, skip doctor review

    doc_amka = random.choice(prescribers)
    emit(f"INSERT IGNORE INTO patient_review_doctor "
         f"(id, hospitalization_id, patient_amka, doctor_amka, medical_care, review_date) "
         f"VALUES ({rev_doc_id}, {h['id']}, {sql_str(h['patient_amka'])}, "
         f"{sql_str(doc_amka)}, {random.randint(1,5)}, {sql_date(review_date)});")
    rev_doc_id += 1
emit()

# ============================================================
# DONE
# ============================================================

emit("SET FOREIGN_KEY_CHECKS = 1;")
emit()
emit("-- ============================================================")
emit("-- Data generation complete")
emit(f"-- Departments:       {len(DEPT_NAMES)}")
emit(f"-- Doctors:           {len(doctors)}")
emit(f"-- Nurses:            120")
emit(f"-- Admin:             60")
emit(f"-- Patients:          200")
emit(f"-- Beds:              ~{bed_id - 1}")
emit(f"-- Shifts:            ~{shift_id - 1}")
emit(f"-- Hospitalizations:  500")
emit(f"-- Lab tests:         200")
emit(f"-- Medical procedures:~{proc_id - 1}")
emit(f"-- Prescriptions:     ~{presc_id - 1}")
emit("-- ============================================================")

# Write output
output_path = "load.sql"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"Done. Written to {output_path}", file=sys.stderr)