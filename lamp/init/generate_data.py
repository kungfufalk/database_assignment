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
"""

import random
import sys
import mysql.connector
from datetime import date, datetime, timedelta, time
from faker import Faker

fake    = Faker('el_GR')   # Greek locale for realistic names
fake_en = Faker('en_US')

random.seed(42)  # reproducible output

# ============================================================
# DATABASE CONNECTION CONFIG
# ============================================================
DB_CONFIG = {
    "host": "127.0.0.1",      # Change to 'mariadb' if running inside docker
    "port": 3306,             # The port mapped in your docker-compose
    "user": "root",
    "password": "your_password",
    "database": "ygeiopolis"
}

def fetch_reference_data():
    """Queries the database for existing reference codes."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Fetching reference data from database...")
        
        # 1. Fetch ICD10 Codes
        cursor.execute("SELECT code FROM icd10_code")
        icd10_codes = [row[0] for row in cursor.fetchall()]

        # 2. Fetch KEN Codes (and their costs/los for logic)
        cursor.execute("SELECT code, base_cost, mean_los_days FROM ken_code")
        ken_codes = cursor.fetchall()

        # 3. Fetch Procedure Catalog Codes
        cursor.execute("SELECT code FROM procedure_catalog")
        proc_codes = [row[0] for row in cursor.fetchall()]

        # 4. Active Substances (for T5 allergy check)
        cursor.execute("SELECT id FROM active_substance")
        active_subtances = [row[0] for row in cursor.fetchall()]

        # 5. Drug IDs
        cursor.execute("SELECT id FROM drug")
        drugs = [row[0] for row in cursor.fetchall()]

        conn.close()
        
        if not icd10_codes or not ken_codes or not proc_codes or not active_subtances or not drugs:
            raise ValueError("Reference tables are empty. Please fill them before running this script.")

        return icd10_codes, ken_codes, proc_codes, active_subtances, drugs

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sys.exit(1)

# ============================================================
# DATA GENERATION
# ============================================================

# Fetch data from DB
ICD10_CODES, KEN_CODES, PROCEDURE_CATALOG_CODES, ACTIVE_SUBSTANCES, DRUGS = fetch_reference_data()

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
# DOMAIN CONSTANTS
# ============================================================

SPECIALTIES = [
    "Cardiology", "Surgery", "Internal Medicine", "Orthopedics",
    "Neurology", "Oncology", "Pulmonology", "Gastroenterology",
    "Nephrology", "Urology", "Gynecology", "Pediatrics",
    "Psychiatry", "Radiology", "Anesthesiology",
]

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

# Clear database tables
emit("-- ------------------------------------------------------------")
emit("-- Clearing all tables before insert")
emit("-- ------------------------------------------------------------")
tables = [
    "patient_review_doctor", "patient_review_hospitalization", "prescription",
    "procedure_staff", "medical_procedure", "lab_test", "hospitalization",
    "triage", "shift_assignment", "shift", "operating_room", "bed",
    "doctor_department", "doctor", "nurse", "admin_staff", "staff",
    "patient", "patient_allergy", "department",
]
for t in tables:
    emit(f"DELETE FROM {t};")
    emit(f"ALTER TABLE {t} AUTO_INCREMENT = 1;")
emit("SET FOREIGN_KEY_CHECKS = 1;")
emit()

# ============================================================
# 1. DEPARTMENTS
# ============================================================

emit("-- Departments")
dept_ids = {}
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

emit("-- Staff + Doctors")
used_amkas = set()
def gen_amka():
    while True:
        a = random_amka()
        if a not in used_amkas:
            used_amkas.add(a)
            return a

doctors = []
ranks_distribution = [
    ("Director",    10),
    ("Registrar_A", 20),
    ("Registrar_B", 25),
    ("Resident",    25),
]
doctor_amkas_by_rank = {r: [] for r, _ in ranks_distribution}
doc_count = 0

for rank, count in ranks_distribution:
    for _ in range(count):
        amka = gen_amka()
        first = fake.first_name()
        last  = fake.last_name()
        birth = random_date(date(1960, 1, 1), date(1995, 12, 31))
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
            'amka': amka, 'first': first, 'last': last, 'birth': birth,
            'hire': hire, 'email': email, 'phone': phone, 'specialty': specialty,
            'rank': rank, 'license_no': license_no,
        })
        doctor_amkas_by_rank[rank].append(amka)
        doc_count += 1

# Enforce T1 and T2 - strictly hierarchical assignment
supervisor_map = {}
for d in doctors:
    if d['rank'] == 'Resident':
        supervisor_map[d['amka']] = random.choice(doctor_amkas_by_rank['Registrar_A'] + doctor_amkas_by_rank['Registrar_B'])
    elif d['rank'] == 'Registrar_B':
        supervisor_map[d['amka']] = random.choice(doctor_amkas_by_rank['Registrar_A'] + doctor_amkas_by_rank['Director'])
    elif d['rank'] == 'Registrar_A':
        supervisor_map[d['amka']] = random.choice(doctor_amkas_by_rank['Director'])
    else:
        supervisor_map[d['amka']] = None  # Directors have no supervisor

emit("-- Doctor subclass rows")
for d in doctors:
    sup = supervisor_map[d['amka']]
    sup_sql = sql_str(sup) if sup else "NULL"
    emit(f"INSERT INTO doctor (amka, license_no, specialty, rank, supervisor_amka) "
         f"VALUES ({sql_str(d['amka'])}, {sql_str(d['license_no'])}, "
         f"{sql_str(d['specialty'])}, {sql_str(d['rank'])}, {sup_sql});")
emit()

# Doctor-Department assignments
emit("-- Doctor-Department assignments")
for d in doctors:
    specialty_dept = next((dept_ids[s] for s, _ in DEPT_NAMES if s == d['specialty']), random.randint(1, len(DEPT_NAMES)))
    depts = {specialty_dept}
    while len(depts) <= random.randint(0, 2):
        depts.add(random.randint(1, len(DEPT_NAMES)))

    for dept_id in depts:
        emit(f"INSERT IGNORE INTO doctor_department (doctor_amka, department_id) "
             f"VALUES ({sql_str(d['amka'])}, {dept_id});")

emit("-- Set department directors")
director_amkas = doctor_amkas_by_rank['Director']
for i, (specialty, _) in enumerate(DEPT_NAMES):
    dir_amka = director_amkas[i % len(director_amkas)]
    emit(f"UPDATE department SET director_amka = {sql_str(dir_amka)} WHERE id = {dept_ids[specialty]};")
emit()

# ============================================================
# 4. NURSES
# ============================================================

emit("-- Staff + Nurses")
nurses = []
for i in range(120):
    amka = gen_amka()
    first = fake.first_name_female()
    last  = fake.last_name()
    birth = random_date(date(1970, 1, 1), date(2000, 12, 31))
    hire  = random_date(date(2005, 1, 1), date(2023, 12, 31))
    rank  = random.choices(['Assistant', 'Nurse', 'Head_Nurse'], weights=[30, 60, 10])[0]
    dept_id = random.randint(1, len(DEPT_NAMES))

    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_date(birth)}, "
         f"{sql_str(f'{fake_en.user_name()}@ygeiopolis.gr')}, {sql_str(fake.phone_number()[:20])}, {sql_date(hire)}, 'nurse');")
    emit(f"INSERT INTO nurse (amka, rank, department_id) VALUES ({sql_str(amka)}, {sql_str(rank)}, {dept_id});")

    nurses.append({'amka': amka, 'rank': rank, 'dept_id': dept_id})
emit()

# ============================================================
# 5. ADMIN STAFF
# ============================================================

emit("-- Staff + Admin")
admins = []
for i in range(60):
    amka = gen_amka()
    first = fake.first_name()
    last  = fake.last_name()
    birth = random_date(date(1965, 1, 1), date(1998, 12, 31))
    hire  = random_date(date(2000, 1, 1), date(2023, 12, 31))
    role  = random.choice(['Secretary', 'Accountant', 'Receptionist', 'HR Officer', 'IT Support', 'Logistics'])
    dept_id = random.randint(1, len(DEPT_NAMES))

    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(first)}, {sql_str(last)}, {sql_date(birth)}, "
         f"{sql_str(f'{fake_en.user_name()}@ygeiopolis.gr')}, {sql_str(fake.phone_number()[:20])}, {sql_date(hire)}, 'admin');")
    emit(f"INSERT INTO admin_staff (amka, role, office, department_id) VALUES ({sql_str(amka)}, {sql_str(role)}, {sql_str(f'Office {random.randint(100, 399)}')}, {dept_id});")

    admins.append({'amka': amka, 'role': role, 'dept_id': dept_id})
emit()

# ============================================================
# 6. BEDS & 7. OPERATING ROOMS
# ============================================================

emit("-- Beds & Operating Rooms")
beds = []
bed_id = 1
for dept_id in range(1, len(DEPT_NAMES) + 1):
    count = random.randint(10, 30)
    for j in range(1, count + 1):
        btype = random.choices(['ICU', 'Single', 'Multi', 'Other'], weights=[10, 20, 60, 10])[0]
        status = random.choices(['Available', 'Occupied', 'Maintenance'], weights=[50, 40, 10])[0]
        emit(f"INSERT INTO bed (id, bed_number, department_id, bed_type, status) "
             f"VALUES ({bed_id}, {sql_str(f'{dept_id:02d}-{j:03d}')}, {dept_id}, {sql_str(btype)}, {sql_str(status)});")
        beds.append({'id': bed_id, 'dept_id': dept_id})
        bed_id += 1

op_rooms = []
for i in range(1, 11):
    rtype = 'OR' if i <= 6 else 'Procedure_Room'
    name  = f"{'Χειρουργείο' if rtype == 'OR' else 'Αίθουσα Επεμβάσεων'} {i}"
    emit(f"INSERT INTO operating_room (id, name, room_type, department_id) "
         f"VALUES ({i}, {sql_str(name)}, {sql_str(rtype)}, {random.randint(1, len(DEPT_NAMES))});")
    op_rooms.append(i)
emit()

# ============================================================
# 8. PATIENTS & 9. PATIENT ALLERGIES
# ============================================================

emit("-- Patients & Allergies")
patients = []
for i in range(200):
    amka = gen_amka()
    emit(f"INSERT INTO patient (amka, first_name, last_name, fathers_name, birth_date, gender, "
         f"weight_kg, height_cm, address, phone, email, occupation, nationality, "
         f"emergency_name, emergency_phone, emergency_rel, insurance) VALUES ("
         f"{sql_str(amka)}, {sql_str(fake.first_name())}, {sql_str(fake.last_name())}, {sql_str(fake.first_name_male())}, "
         f"{sql_date(random_date(date(1940, 1, 1), date(2005, 12, 31)))}, {sql_str(random.choice(['M', 'F']))}, "
         f"{round(random.uniform(50, 120), 1)}, {round(random.uniform(155, 195), 1)}, "
         f"{sql_str(fake.address().replace(chr(10), ', ')[:255])}, {sql_str(fake.phone_number()[:20])}, "
         f"{sql_str(f'{fake_en.user_name()}@gmail.com')}, {sql_str(random.choice(['Engineer', 'Teacher', 'Retired']))}, "
         f"{sql_str(random.choice(['Greek', 'Greek', 'Albanian']))}, "
         f"{sql_str(fake.name())}, {sql_str(fake.phone_number()[:20])}, {sql_str(random.choice(['Spouse', 'Child']))}, "
         f"{sql_str(random.choices(['EFKA', 'Private', 'Uninsured'], weights=[50, 30, 20])[0])});")
    patients.append({'amka': amka})

allergy_patients = random.sample(patients, 40)
allergy_amkas = {p['amka'] for p in allergy_patients}
for p in allergy_patients:
    num_allergies = random.randint(1, 3)
    for sid in random.sample(ACTIVE_SUBSTANCES, num_allergies):
        emit(f"INSERT IGNORE INTO patient_allergy (patient_amka, substance_id) "
             f"VALUES ({sql_str(p['amka'])}, {sid});")
emit()

# ============================================================
# 10 & 11. SHIFTS AND ASSIGNMENTS (ENFORCING T6, T7, T8)
# ============================================================

emit("-- Shifts and Strictly Verified Assignments")
shift_start = date(2025, 1, 1)
shift_end   = date(2025, 3, 31)

shifts = []
shift_id = 1
current = shift_start
while current <= shift_end:
    for dept_id in range(1, len(DEPT_NAMES) + 1):
        for stype in ['Morning', 'Afternoon', 'Night']:
            emit(f"INSERT INTO shift (id, department_id, shift_date, shift_type) "
                 f"VALUES ({shift_id}, {dept_id}, {sql_date(current)}, {sql_str(stype)});")
            shifts.append({'id': shift_id, 'dept_id': dept_id, 'date': current, 'type': stype})
            shift_id += 1
    current += timedelta(days=1)

# Staff scheduling states
staff_state = {}
for s in doctors + nurses + admins:
    staff_state[s['amka']] = {'monthly': {}, 'last_end': datetime.min, 'night_dates': set()}

def get_shift_times(sdate, stype):
    base = datetime.combine(sdate, datetime.min.time())
    if stype == 'Morning':
        return base + timedelta(hours=7), base + timedelta(hours=15)
    elif stype == 'Afternoon':
        return base + timedelta(hours=15), base + timedelta(hours=23)
    elif stype == 'Night':
        return base + timedelta(hours=23), base + timedelta(hours=31)

def can_assign(amka, sdate, stype, staff_type):
    state = staff_state[amka]
    key = (sdate.year, sdate.month)
    
    # T6: Monthly Limits
    limit = {'doctor': 15, 'nurse': 20, 'admin': 25}.get(staff_type, 999)
    if state['monthly'].get(key, 0) >= limit: return False
        
    # T7: 8-Hour Minimum Rest Check
    new_start, new_end = get_shift_times(sdate, stype)
    if state['last_end'] != datetime.min:
        diff_hours = (new_start - state['last_end']).total_seconds() / 3600.0
        if diff_hours < 8: return False
            
    # T8: Max 3 Consecutive Nights Check
    if stype == 'Night':
        d1, d2, d3 = sdate - timedelta(days=1), sdate - timedelta(days=2), sdate - timedelta(days=3)
        if d1 in state['night_dates'] and d2 in state['night_dates'] and d3 in state['night_dates']: return False
            
    return True

def record_assign(amka, sdate, stype):
    state = staff_state[amka]
    key = (sdate.year, sdate.month)
    state['monthly'][key] = state['monthly'].get(key, 0) + 1
    _, new_end = get_shift_times(sdate, stype)
    if new_end > state['last_end']: state['last_end'] = new_end
    if stype == 'Night': state['night_dates'].add(sdate)

sa_id = 1
for shift in shifts:
    sdate, stype, sid = shift['date'], shift['type'], shift['id']

    available_docs = [d for d in doctors if can_assign(d['amka'], sdate, stype, 'doctor')]
    available_nurses = [n for n in nurses if can_assign(n['amka'], sdate, stype, 'nurse')]
    available_admins = [a for a in admins if can_assign(a['amka'], sdate, stype, 'admin')]

    chosen_docs   = random.sample(available_docs,   min(random.randint(3, 5), len(available_docs)))
    chosen_nurses = random.sample(available_nurses, min(random.randint(6, 9), len(available_nurses)))
    chosen_admins = random.sample(available_admins, min(random.randint(2, 3), len(available_admins)))

    # Fix Rank Requirements Check
    if any(d['rank'] == 'Resident' for d in chosen_docs) and not any(d['rank'] in ('Registrar_A', 'Director') for d in chosen_docs):
        seniors = [d for d in available_docs if d['rank'] in ('Registrar_A', 'Director')]
        if seniors: chosen_docs.append(random.choice(seniors))

    for item, staff_amka in [(chosen_docs, 'doctor'), (chosen_nurses, 'nurse'), (chosen_admins, 'admin')]:
        for mem in item:
            emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) VALUES ({sa_id}, {sid}, {sql_str(mem['amka'])});")
            record_assign(mem['amka'], sdate, stype)
            sa_id += 1
emit()

# ============================================================
# 12 & 13. TRIAGE AND HOSPITALIZATIONS
# ============================================================

emit("-- Triage & Hospitalizations")
triage_records = []
er_nurses = [n for n in nurses if n['dept_id'] == dept_ids.get('Emergency', 15)] or nurses[:10]
triage_id = 1
triage_start, triage_end = date(2023, 1, 1), date(2024, 12, 31)

for i in range(600):
    patient = random.choice(patients)
    arrival = datetime.combine(random_date(triage_start, triage_end), datetime.min.time()) + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
    urgency = random.choices([1,2,3,4,5], weights=[5, 15, 30, 30, 20])[0]
    service_time = arrival + timedelta(minutes={1: 5, 2: 15, 3: 30, 4: 60, 5: 120}[urgency] + random.randint(0, 30))
    outcome = random.choices(['Admitted', 'Discharged'], weights=[40, 60])[0]

    emit(f"INSERT INTO triage (id, patient_amka, nurse_amka, arrival_time, symptoms, urgency_level, outcome, service_time) "
         f"VALUES ({triage_id}, {sql_str(patient['amka'])}, {sql_str(random.choice(er_nurses)['amka'])}, "
         f"{sql_datetime(arrival)}, 'Symptoms recorded at triage', {urgency}, {sql_str(outcome)}, {sql_datetime(service_time)});")
    triage_records.append({'id': triage_id, 'patient_amka': patient['amka'], 'outcome': outcome, 'arrival': arrival})
    triage_id += 1

hosp_records = []
hosp_id = 1
admitted_triages = [t for t in triage_records if t['outcome'] == 'Admitted']

for i in range(500):
    patient = patients[i // 5] if i < 30 and i % 5 == 0 else random.choice(patients)
    dept_id = random.randint(1, 5) if i < 30 and i % 5 == 0 else random.randint(1, len(DEPT_NAMES))
    bed = random.choice([b for b in beds if b['dept_id'] == dept_id] or beds[:5])
    
    triage_ref = None
    adm_date = random_date(triage_start, triage_end)
    if i < len(admitted_triages):
        triage_ref = admitted_triages[i]['id']
        adm_date = max(admitted_triages[i]['arrival'].date(), triage_start)

    ken = random.choice(KEN_CODES)
    actual_los = random.choices(range(1, 20), weights=[5,8,12,15,12,10,8,6,5,4,3,3,2,2,2,1,1,1,1])[0]
    disc_date = min(adm_date + timedelta(days=actual_los), date(2025, 6, 30))
    surcharge = round(max(0, actual_los - ken[2]) * round(ken[1] / ken[2], 2), 2)

    emit(f"INSERT INTO hospitalization (id, patient_amka, bed_id, department_id, triage_id, admission_date, discharge_date, admission_icd10, discharge_icd10, ken_code, base_cost, surcharge) "
         f"VALUES ({hosp_id}, {sql_str(patient['amka'])}, {bed['id']}, {dept_id}, {'NULL' if triage_ref is None else triage_ref}, "
         f"{sql_date(adm_date)}, {sql_date(disc_date)}, {sql_str(random.choice(ICD10_CODES))}, {sql_str(random.choice(ICD10_CODES))}, "
         f"{sql_str(ken[0])}, {ken[1]}, {surcharge});")
    hosp_records.append({'id': hosp_id, 'patient_amka': patient['amka'], 'dept_id': dept_id, 'adm_date': adm_date, 'disc_date': disc_date})
    hosp_id += 1
emit()

# ============================================================
# 14. LAB TESTS
# ============================================================

emit("-- Lab Tests")
lt_id = 1
for h in random.sample(hosp_records, min(200, len(hosp_records))):
    tdate = h['adm_date'] + timedelta(days=random.randint(0, max(1, (h['disc_date'] - h['adm_date']).days)))
    emit(f"INSERT INTO lab_test (id, hospitalization_id, ordering_doctor_amka, code, test_type, test_date, result_text, result_value, result_unit, cost) "
         f"VALUES ({lt_id}, {h['id']}, {sql_str(random.choice(doctors)['amka'])}, {sql_str(f'LAB{random.randint(1000,9999)}')}, "
         f"{sql_str(random.choice(['Haematological', 'Biochemical', 'Imaging']))}, {sql_date(tdate)}, 'Result within normal range', "
         f"{round(random.uniform(0.1, 999.9), 2)}, {sql_str(random.choice(['mg/dL', 'mmol/L', 'U/L']))}, {round(random.uniform(20, 300), 2)});")
    lt_id += 1
emit()

# ============================================================
# 15. MEDICAL PROCEDURES (ENFORCING T3 & T4)
# ============================================================

emit("-- Medical Procedures")
proc_id = 1
room_schedule = {r: [] for r in op_rooms}
doctor_schedule = {}

def is_free(schedule, key, start_dt, end_dt):
    return all(end_dt <= s or start_dt >= e for s, e in schedule.get(key, []))

for h in random.sample(hosp_records, min(150, len(hosp_records))):
    duration = random.randint(30, 240)
    proc_date = h['adm_date'] + timedelta(days=random.randint(0, max(1, (h['disc_date'] - h['adm_date']).days)))
    start_dt = datetime.combine(proc_date, datetime.min.time()) + timedelta(hours=random.randint(8, 16))
    end_dt = start_dt + timedelta(minutes=duration)

    room_id = next((r for r in random.sample(op_rooms, len(op_rooms)) if is_free(room_schedule, r, start_dt, end_dt)), None)
    surgeon = next((d for d in random.sample(doctors, len(doctors)) if is_free(doctor_schedule, d['amka'], start_dt, end_dt)), None)
    if not room_id or not surgeon: continue

    room_schedule[room_id].append((start_dt, end_dt))
    doctor_schedule.setdefault(surgeon['amka'], []).append((start_dt, end_dt))

    emit(f"INSERT INTO medical_procedure (id, catalog_code, hospitalization_id, start_datetime, duration_minutes, cost, operating_room_id, primary_surgeon_amka) "
         f"VALUES ({proc_id}, {sql_str(random.choice(PROCEDURE_CATALOG_CODES))}, {h['id']}, {sql_datetime(start_dt)}, {duration}, {round(random.uniform(500, 8000), 2)}, {room_id}, {sql_str(surgeon['amka'])});")

    assistant_pool = [a['amka'] for a in doctors + nurses if a['amka'] != surgeon['amka']]
    for asst_amka in random.sample(assistant_pool, random.randint(1, 2)):
        emit(f"INSERT IGNORE INTO procedure_staff (procedure_id, staff_amka, role) VALUES ({proc_id}, {sql_str(asst_amka)}, 'Assistant');")
    proc_id += 1
emit()

# ============================================================
# 16. PRESCRIPTIONS (ENFORCING T5)
# ============================================================

emit("-- Prescriptions")
presc_id = 1
presc_keys = set()
presc_records = []

# Guard against Trigger 5: Never prescribe random drugs to allergic patients
safe_hosps = [h for h in hosp_records if h['patient_amka'] not in allergy_amkas]

for h in random.sample(safe_hosps, min(300, len(safe_hosps))):
    doc = random.choice(doctors)
    drug_id = int(random.sample(DRUGS, 1)[0])
    start = h['adm_date'] + timedelta(days=random.randint(0, 2))
    
    key = (doc['amka'], h['patient_amka'], drug_id, start)
    if key in presc_keys: continue
    presc_keys.add(key)

    emit(f"INSERT INTO prescription (id, hospitalization_id, doctor_amka, patient_amka, drug_id, start_date, end_date, dosage, frequency) "
         f"VALUES ({presc_id}, {h['id']}, {sql_str(doc['amka'])}, {sql_str(h['patient_amka'])}, {drug_id}, {sql_date(start)}, {sql_date(start + timedelta(days=random.randint(3, 14)))}, "
         f"{sql_str(random.choice(['1 tablet', '2 tablets', '500mg']))}, {sql_str(random.choice(['Once daily', 'Twice daily']))});")
    
    presc_records.append({'hospitalization_id': h['id'], 'doctor_amka': doc['amka'], 'patient_amka': h['patient_amka']})
    presc_id += 1
emit()

# ============================================================
# 17. PATIENT REVIEWS (ENFORCING T9 & T10)
# ============================================================

emit("-- Patient Reviews")
rev_hosp_id, rev_doc_id = 1, 1

hosp_prescribers = {}
for p in presc_records:
    hosp_prescribers.setdefault(p['hospitalization_id'], set()).add(p['doctor_amka'])

# Trigger 9 constraint: Only Completed hospitalizations
completed = [h for h in hosp_records if h['disc_date'] is not None]

for h in random.sample(completed, min(200, len(completed))):
    review_date = h['disc_date'] + timedelta(days=random.randint(1, 30))
    emit(f"INSERT IGNORE INTO patient_review_hospitalization (id, hospitalization_id, patient_amka, nursing_care, cleanliness, food, overall_experience, review_date) "
         f"VALUES ({rev_hosp_id}, {h['id']}, {sql_str(h['patient_amka'])}, {random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, {sql_date(review_date)});")
    rev_hosp_id += 1

    # Trigger 10 constraint: You can only review doctors who prescribed to you in this hospitalization
    prescribers = list(hosp_prescribers.get(h['id'], []))
    if not prescribers: continue

    emit(f"INSERT IGNORE INTO patient_review_doctor (id, hospitalization_id, patient_amka, doctor_amka, medical_care, review_date) "
         f"VALUES ({rev_doc_id}, {h['id']}, {sql_str(h['patient_amka'])}, {sql_str(random.choice(prescribers))}, {random.randint(1,5)}, {sql_date(review_date)});")
    rev_doc_id += 1
emit()

# ============================================================
# DONE
# ============================================================

emit("SET FOREIGN_KEY_CHECKS = 1;")
output_path = "generated_data.sql"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"Done. Written to {output_path}", file=sys.stderr)