#!/usr/bin/env python3
"""
Ygeiopolis Hospital - Synthetic Data Generator
Generates generated_data.sql with all synthetic hospital data.

The following tables are NOT populated here — load their official files first:
    - icd10_code        (from MoH file, fdl=3091)
    - ken_code          (from MoH file, fdl=3092)
    - procedure_catalog (from MoH file, fdl=1930)
    - drug              (from EMA Article 57 xlsx)
    - active_substance  (from EMA Article 57 xlsx)
    - drug_active_substance (from EMA Article 57 xlsx)

Query coverage guaranteed:
    Q01  - hospitalizations across depts, 2 years, multiple KEN codes, all insurance types
    Q02  - doctors per specialty, with shifts in 2025 and surgeries this year
    Q03  - 5 patients each hospitalized 4 times in the same department
    Q04  - doctor reviews + hospitalization reviews linked via prescriptions
    Q05  - 10 young doctors (born 1991-1999) with surgical procedures in 2025
    Q06  - target patient has multiple hospitalizations, prescriptions and reviews
    Q07  - 40 patients with allergies to real substance IDs; drugs contain those substances
    Q08  - most staff are not assigned every shift, so unscheduled staff always exist
    Q09  - 3 patient pairs each with identical total hospitalized days (16) in 2024
    Q10  - 20 hospitalizations each with 3 co-prescribed drugs (substance pairs guaranteed)
    Q11  - one doctor has 20 procedures this year; all others have fewer (diff >= 5)
    Q12  - shifts cover Jan-Mar 2025 with doctors/nurses/admin broken down by sub-category
    Q13  - all Registrar_A have Director supervisors -> full 4-level chain guaranteed
    Q14  - 3 ICD-10 categories with exactly 5 admissions in both 2023 and 2024
    Q15  - 600 triage records with controlled distribution across all 5 urgency levels
"""

import random
import sys
import mysql.connector
from datetime import date, datetime, timedelta, time
from faker import Faker

fake    = Faker('el_GR')
fake_en = Faker('en_US')

random.seed(42)

# ============================================================
# DATABASE CONNECTION CONFIG
# ============================================================
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     3306,
    "user":     "root",
    "password": "your_password",
    "database": "ygeiopolis"
}

def fetch_reference_data():
    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Fetching reference data from database...", file=sys.stderr)

        cursor.execute("SELECT code FROM icd10_code")
        icd10_codes = [row[0] for row in cursor.fetchall()]

        # (code, base_cost, mean_los_days)
        cursor.execute("SELECT code, base_cost, mean_los_days FROM ken_code")
        ken_codes = cursor.fetchall()

        cursor.execute("SELECT code FROM procedure_catalog")
        proc_codes = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT id FROM active_substance")
        active_substances = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT id FROM drug")
        drugs = [row[0] for row in cursor.fetchall()]

        # Drug -> substance mapping for allergy-safe prescriptions (T5)
        cursor.execute("SELECT drug_id, substance_id FROM drug_active_substance")
        drug_substance_rows = cursor.fetchall()

        conn.close()

        if not icd10_codes or not ken_codes or not proc_codes or not active_substances or not drugs:
            raise ValueError("Reference tables are empty. Load reference data first.")

        print(f"  icd10_codes={len(icd10_codes)}, ken_codes={len(ken_codes)}, "
              f"proc_codes={len(proc_codes)}, substances={len(active_substances)}, "
              f"drugs={len(drugs)}", file=sys.stderr)

        return icd10_codes, ken_codes, proc_codes, active_substances, drugs, drug_substance_rows

    except mysql.connector.Error as err:
        print(f"DB Error: {err}", file=sys.stderr)
        sys.exit(1)

(ICD10_CODES, KEN_CODES, PROCEDURE_CATALOG_CODES,
 ACTIVE_SUBSTANCES, DRUGS, DRUG_SUBSTANCE_ROWS) = fetch_reference_data()

# Drug -> set of substance_ids (for allergy check)
drug_to_substances = {}
for drug_id, sub_id in DRUG_SUBSTANCE_ROWS:
    drug_to_substances.setdefault(drug_id, set()).add(sub_id)

# ICD-10 category -> list of codes (for Q14)
ICD10_BY_CATEGORY = {}
for code in ICD10_CODES:
    ICD10_BY_CATEGORY.setdefault(code[:3], []).append(code)

# ============================================================
# HELPERS
# ============================================================

output_lines = []

def emit(line=""):
    output_lines.append(line)

def sql_str(val):
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

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

used_amkas = set()
def gen_amka():
    while True:
        a = random_amka()
        if a not in used_amkas:
            used_amkas.add(a)
            return a

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
    ("Cardiology",       "Καρδιολογική Κλινική"),
    ("Surgery",          "Χειρουργική Κλινική"),
    ("Internal Medicine","Παθολογική Κλινική"),
    ("Orthopedics",      "Ορθοπεδική Κλινική"),
    ("Neurology",        "Νευρολογική Κλινική"),
    ("Oncology",         "Ογκολογική Κλινική"),
    ("Pulmonology",      "Πνευμονολογική Κλινική"),
    ("Gastroenterology", "Γαστρεντερολογική Κλινική"),
    ("Nephrology",       "Νεφρολογική Κλινική"),
    ("Urology",          "Ουρολογική Κλινική"),
    ("Gynecology",       "Γυναικολογική Κλινική"),
    ("Pediatrics",       "Παιδιατρική Κλινική"),
    ("Psychiatry",       "Ψυχιατρική Κλινική"),
    ("ICU",              "Μονάδα Εντατικής Θεραπείας"),
    ("Emergency",        "Τμήμα Επειγόντων Περιστατικών"),
]

NUM_DEPTS = len(DEPT_NAMES)

# ============================================================
# HEADER
# ============================================================

emit("-- ============================================================")
emit("-- Ygeiopolis Hospital - Synthetic Data")
emit("-- Generated by generate_data.py")
emit("-- ============================================================")
emit()
emit("SET FOREIGN_KEY_CHECKS = 0;")
emit("SET NAMES utf8mb4;")
emit()

# Clear tables in safe reverse-dependency order
emit("-- Clear tables")
for t in [
    "patient_review_doctor", "patient_review_hospitalization",
    "prescription", "procedure_staff", "medical_procedure",
    "lab_test", "hospitalization", "triage",
    "shift_assignment", "shift", "operating_room", "bed",
    "doctor_department", "doctor", "nurse", "admin_staff",
    "staff", "patient", "patient_allergy", "department",
]:
    emit(f"DELETE FROM {t};")
    emit(f"ALTER TABLE {t} AUTO_INCREMENT = 1;")
emit("SET FOREIGN_KEY_CHECKS = 1;")
emit()

# ============================================================
# 1. DEPARTMENTS
# ============================================================

emit("-- Departments")
dept_ids = {}   # specialty_key -> dept id
for i, (specialty, greek_name) in enumerate(DEPT_NAMES, 1):
    dept_ids[specialty] = i
    emit(f"INSERT INTO department (id, name, description, bed_count, floor_building, director_amka) "
         f"VALUES ({i}, {sql_str(greek_name)}, "
         f"{sql_str(greek_name + ' - Γενικό Νοσοκομείο Υγειόπολης')}, "
         f"{random.randint(15, 50)}, "
         f"{sql_str(f'Floor {random.randint(1,6)}, Building {random.choice(["A","B","C"])}')},"
         f" NULL);")
emit()

# ============================================================
# 2. DOCTORS
# Q02:  doctors per specialty with shifts + procedures in 2025
# Q05:  young doctors (born 1991-1999) with procedures
# Q11:  one top surgeon + others with fewer procedures
# Q13:  full 4-level hierarchy guaranteed (Director->RegA->RegB->Resident)
# ============================================================

emit("-- Staff + Doctors")
doctors = []
ranks = [("Director", 10), ("Registrar_A", 20), ("Registrar_B", 25), ("Resident", 25)]
doctor_amkas_by_rank = {r: [] for r, _ in ranks}
young_count = 0

for rank, count in ranks:
    for idx in range(count):
        amka       = gen_amka()
        specialty  = random.choice(SPECIALTIES)
        license_no = f"ΙΑΤ{random.randint(100000, 999999)}"
        hire       = random_date(date(2000, 1, 1), date(2023, 12, 31))
        email      = f"{fake_en.user_name()}@ygeiopolis.gr"
        phone      = fake.phone_number()[:20]

        # Q05: ensure 10 young doctors exist
        if rank in ('Resident', 'Registrar_B') and young_count < 10:
            birth = random_date(date(1991, 1, 1), date(1999, 12, 31))
            young_count += 1
        else:
            birth = random_date(date(1960, 1, 1), date(1990, 12, 31))

        # Assign supervisors in Python before SQL — satisfies T1 INSERT trigger
        supervisor_amka = None
        if rank == 'Resident':
            pool = doctor_amkas_by_rank['Registrar_A'] + doctor_amkas_by_rank['Registrar_B']
            supervisor_amka = random.choice(pool)
        elif rank == 'Registrar_B':
            pool = doctor_amkas_by_rank['Registrar_A'] + doctor_amkas_by_rank['Director']
            supervisor_amka = random.choice(pool)
        elif rank == 'Registrar_A':
            # All get a Director — guarantees 4-level chains for Q13
            supervisor_amka = random.choice(doctor_amkas_by_rank['Director'])
        # Directors: None

        doctors.append({
            'amka': amka, 'first': fake.first_name(), 'last': fake.last_name(),
            'birth': birth, 'hire': hire, 'email': email, 'phone': phone,
            'specialty': specialty, 'rank': rank,
            'license_no': license_no, 'supervisor_amka': supervisor_amka,
        })
        doctor_amkas_by_rank[rank].append(amka)

# Emit in rank order: supervisors must exist before subordinates (T1/T2)
for rank in ['Director', 'Registrar_A', 'Registrar_B', 'Resident']:
    for d in [x for x in doctors if x['rank'] == rank]:
        emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
             f"VALUES ({sql_str(d['amka'])}, {sql_str(d['first'])}, {sql_str(d['last'])}, "
             f"{sql_date(d['birth'])}, {sql_str(d['email'])}, {sql_str(d['phone'])}, "
             f"{sql_date(d['hire'])}, 'doctor');")
        emit(f"INSERT INTO doctor (amka, license_no, specialty, rank, supervisor_amka) "
             f"VALUES ({sql_str(d['amka'])}, {sql_str(d['license_no'])}, "
             f"{sql_str(d['specialty'])}, {sql_str(d['rank'])}, "
             f"{sql_str(d['supervisor_amka'])});")
emit()

# Doctor-Department (many-to-many)
emit("-- Doctor-Department assignments")
for d in doctors:
    primary = dept_ids.get(d['specialty'], random.randint(1, NUM_DEPTS))
    depts   = {primary}
    while len(depts) <= random.randint(0, 2):
        depts.add(random.randint(1, NUM_DEPTS))
    for did in depts:
        emit(f"INSERT IGNORE INTO doctor_department (doctor_amka, department_id) "
             f"VALUES ({sql_str(d['amka'])}, {did});")

emit("-- Set department directors")
dirs = doctor_amkas_by_rank['Director']
for i, (specialty, _) in enumerate(DEPT_NAMES):
    emit(f"UPDATE department SET director_amka = {sql_str(dirs[i % len(dirs)])} "
         f"WHERE id = {dept_ids[specialty]};")
emit()

# ============================================================
# 3. NURSES  (Q12: needs all 3 ranks represented)
# ============================================================

emit("-- Staff + Nurses")
nurses = []
for _ in range(120):
    amka    = gen_amka()
    rank    = random.choices(['Assistant','Nurse','Head_Nurse'], weights=[30,60,10])[0]
    dept_id = random.randint(1, NUM_DEPTS)
    birth   = random_date(date(1970, 1, 1), date(2000, 12, 31))
    hire    = random_date(date(2005, 1, 1), date(2023, 12, 31))
    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(fake.first_name_female())}, {sql_str(fake.last_name())}, "
         f"{sql_date(birth)}, {sql_str(fake_en.user_name() + '@ygeiopolis.gr')}, "
         f"{sql_str(fake.phone_number()[:20])}, {sql_date(hire)}, 'nurse');")
    emit(f"INSERT INTO nurse (amka, rank, department_id) "
         f"VALUES ({sql_str(amka)}, {sql_str(rank)}, {dept_id});")
    nurses.append({'amka': amka, 'rank': rank, 'dept_id': dept_id})
emit()

# ============================================================
# 4. ADMIN STAFF  (Q12: needs all roles represented)
# ============================================================

emit("-- Staff + Admin")
admins     = []
admin_roles = ['Secretary','Accountant','Receptionist','HR Officer','IT Support','Logistics']
for _ in range(60):
    amka    = gen_amka()
    role    = random.choice(admin_roles)
    dept_id = random.randint(1, NUM_DEPTS)
    birth   = random_date(date(1965, 1, 1), date(1998, 12, 31))
    hire    = random_date(date(2000, 1, 1), date(2023, 12, 31))
    emit(f"INSERT INTO staff (amka, first_name, last_name, birth_date, email, phone, hire_date, staff_type) "
         f"VALUES ({sql_str(amka)}, {sql_str(fake.first_name())}, {sql_str(fake.last_name())}, "
         f"{sql_date(birth)}, {sql_str(fake_en.user_name() + '@ygeiopolis.gr')}, "
         f"{sql_str(fake.phone_number()[:20])}, {sql_date(hire)}, 'admin');")
    emit(f"INSERT INTO admin_staff (amka, role, office, department_id) "
         f"VALUES ({sql_str(amka)}, {sql_str(role)}, "
         f"{sql_str(f'Office {random.randint(100,399)}')}, {dept_id});")
    admins.append({'amka': amka, 'role': role, 'dept_id': dept_id})
emit()

# ============================================================
# 5. BEDS & OPERATING ROOMS
# ============================================================

emit("-- Beds")
beds   = []
bed_id = 1
for dept_id in range(1, NUM_DEPTS + 1):
    for j in range(1, random.randint(15, 30) + 1):
        btype  = random.choices(['ICU','Single','Multi','Other'], weights=[10,20,60,10])[0]
        status = random.choices(['Available','Occupied','Maintenance'], weights=[50,40,10])[0]
        emit(f"INSERT INTO bed (id, bed_number, department_id, bed_type, status) "
             f"VALUES ({bed_id}, {sql_str(f'{dept_id:02d}-{j:03d}')}, "
             f"{dept_id}, {sql_str(btype)}, {sql_str(status)});")
        beds.append({'id': bed_id, 'dept_id': dept_id})
        bed_id += 1

emit("-- Operating Rooms")
op_rooms = list(range(1, 11))
for i in op_rooms:
    rtype = 'OR' if i <= 6 else 'Procedure_Room'
    name  = f"{'Χειρουργείο' if rtype == 'OR' else 'Αίθουσα Επεμβάσεων'} {i}"
    emit(f"INSERT INTO operating_room (id, name, room_type, department_id) "
         f"VALUES ({i}, {sql_str(name)}, {sql_str(rtype)}, "
         f"{random.randint(1, NUM_DEPTS)});")
emit()

# ============================================================
# 6. PATIENTS & ALLERGIES
# Q07: 40 patients with allergies to real substance IDs
# Q10: allergy patients excluded from multi-drug prescriptions
# ============================================================

emit("-- Patients")
patients     = []
allergy_map  = {}   # amka -> set of substance_ids
allergy_amkas = set()

for i in range(200):
    amka      = gen_amka()
    insurance = random.choices(
        ['EFKA','Private','Uninsured','Other'],
        weights=[50, 30, 15, 5]
    )[0]
    birth = random_date(date(1940, 1, 1), date(2005, 12, 31))
    emit(f"INSERT INTO patient (amka, first_name, last_name, fathers_name, birth_date, gender, "
         f"weight_kg, height_cm, address, phone, email, occupation, nationality, "
         f"emergency_name, emergency_phone, emergency_rel, insurance) VALUES ("
         f"{sql_str(amka)}, {sql_str(fake.first_name())}, {sql_str(fake.last_name())}, "
         f"{sql_str(fake.first_name_male())}, {sql_date(birth)}, "
         f"{sql_str(random.choice(['M','F']))}, "
         f"{round(random.uniform(50,120),1)}, {round(random.uniform(155,195),1)}, "
         f"{sql_str(fake.address().replace(chr(10),', ')[:255])}, "
         f"{sql_str(fake.phone_number()[:20])}, "
         f"{sql_str(fake_en.user_name() + '@gmail.com')}, "
         f"{sql_str(random.choice(['Engineer','Teacher','Retired','Doctor','Student']))}, "
         f"{sql_str(random.choice(['Greek','Greek','Albanian','German']))}, "
         f"{sql_str(fake.name())}, {sql_str(fake.phone_number()[:20])}, "
         f"{sql_str(random.choice(['Spouse','Parent','Child','Sibling']))}, "
         f"{sql_str(insurance)});")
    patients.append({'amka': amka, 'insurance': insurance})

# Q07: 40 allergy patients — use first 50 substance IDs for determinism
sub_pool = ACTIVE_SUBSTANCES[:min(50, len(ACTIVE_SUBSTANCES))]
for p in random.sample(patients, 40):
    subs = random.sample(sub_pool, random.randint(1, 3))
    allergy_map[p['amka']]  = set(subs)
    allergy_amkas.add(p['amka'])
    for sid in subs:
        emit(f"INSERT IGNORE INTO patient_allergy (patient_amka, substance_id) "
             f"VALUES ({sql_str(p['amka'])}, {sid});")
emit()

# ============================================================
# 7. SHIFTS & ASSIGNMENTS  (Jan-Mar 2025)
# Q02: doctors need shifts in 2025
# Q08: most staff unassigned on any given shift — query returns them naturally
# Q12: full breakdown available for any week in this range
# ============================================================

emit("-- Shifts (Jan-Mar 2025)")
shifts   = []
shift_id = 1
current  = date(2025, 1, 1)
while current <= date(2025, 3, 31):
    for dept_id in range(1, NUM_DEPTS + 1):
        for stype in ['Morning', 'Afternoon', 'Night']:
            emit(f"INSERT INTO shift (id, department_id, shift_date, shift_type) "
                 f"VALUES ({shift_id}, {dept_id}, {sql_date(current)}, {sql_str(stype)});")
            shifts.append({'id': shift_id, 'dept_id': dept_id,
                           'date': current, 'type': stype})
            shift_id += 1
    current += timedelta(days=1)

def get_shift_window(sdate, stype):
    base = datetime.combine(sdate, datetime.min.time())
    if stype == 'Morning':   return base + timedelta(hours=7),  base + timedelta(hours=15)
    if stype == 'Afternoon': return base + timedelta(hours=15), base + timedelta(hours=23)
    if stype == 'Night':     return base + timedelta(hours=23), base + timedelta(hours=31)

# Per-staff scheduling state (T6/T7/T8)
staff_state = {}
for s in doctors + nurses + admins:
    staff_state[s['amka']] = {
        'monthly':     {},
        'last_end':    datetime.min,
        'night_dates': set(),
    }

def can_assign(amka, sdate, stype, staff_type):
    st    = staff_state[amka]
    key   = (sdate.year, sdate.month)
    limit = {'doctor': 15, 'nurse': 20, 'admin': 25}[staff_type]
    if st['monthly'].get(key, 0) >= limit:
        return False
    new_start, _ = get_shift_window(sdate, stype)
    if (new_start - st['last_end']).total_seconds() < 8 * 3600:
        return False
    if stype == 'Night':
        if all((sdate - timedelta(days=k)) in st['night_dates'] for k in [1, 2, 3]):
            return False
    return True

def record_assign(amka, sdate, stype, staff_type):
    st  = staff_state[amka]
    key = (sdate.year, sdate.month)
    st['monthly'][key] = st['monthly'].get(key, 0) + 1
    _, new_end = get_shift_window(sdate, stype)
    if new_end > st['last_end']:
        st['last_end'] = new_end
    if stype == 'Night':
        st['night_dates'].add(sdate)

emit("-- Shift Assignments")
sa_id = 1
for shift in shifts:
    sdate, stype, sid = shift['date'], shift['type'], shift['id']

    avail_d = [d for d in doctors if can_assign(d['amka'], sdate, stype, 'doctor')]
    avail_n = [n for n in nurses  if can_assign(n['amka'], sdate, stype, 'nurse')]
    avail_a = [a for a in admins  if can_assign(a['amka'], sdate, stype, 'admin')]

    chosen_d = random.sample(avail_d, min(random.randint(3, 5), len(avail_d)))
    chosen_n = random.sample(avail_n, min(random.randint(6, 9), len(avail_n)))
    chosen_a = random.sample(avail_a, min(random.randint(2, 3), len(avail_a)))

    # Resident + senior rule
    if any(d['rank'] == 'Resident' for d in chosen_d):
        if not any(d['rank'] in ('Registrar_A','Director') for d in chosen_d):
            seniors = [d for d in avail_d if d['rank'] in ('Registrar_A','Director')]
            if seniors:
                chosen_d.append(random.choice(seniors))

    for mem in chosen_d:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(mem['amka'])});")
        record_assign(mem['amka'], sdate, stype, 'doctor')
        sa_id += 1
    for mem in chosen_n:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(mem['amka'])});")
        record_assign(mem['amka'], sdate, stype, 'nurse')
        sa_id += 1
    for mem in chosen_a:
        emit(f"INSERT IGNORE INTO shift_assignment (id, shift_id, staff_amka) "
             f"VALUES ({sa_id}, {sid}, {sql_str(mem['amka'])});")
        record_assign(mem['amka'], sdate, stype, 'admin')
        sa_id += 1
emit()

# ============================================================
# 8. TRIAGE
# Q15: controlled urgency distribution, service_time always set
# ============================================================

emit("-- Triage")
triage_records = []
er_nurses = ([n for n in nurses if n['dept_id'] == dept_ids.get('Emergency', 15)]
             or nurses[:10])
triage_id    = 1
triage_start = date(2023, 1, 1)
triage_end   = date(2024, 12, 31)

# Q15: at least 30 cases per urgency level
urgency_pool = []
for urg, cnt in {1: 30, 2: 60, 3: 150, 4: 200, 5: 160}.items():
    urgency_pool.extend([urg] * cnt)
random.shuffle(urgency_pool)

wait_base = {1: 5, 2: 15, 3: 30, 4: 60, 5: 120}

for i in range(600):
    patient  = random.choice(patients)
    urgency  = urgency_pool[i] if i < len(urgency_pool) else random.randint(1, 5)
    arrival  = (datetime.combine(random_date(triage_start, triage_end), datetime.min.time())
                + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59)))
    wait_min     = wait_base[urgency] + random.randint(0, 30)
    service_time = arrival + timedelta(minutes=wait_min)
    outcome      = random.choices(['Admitted','Discharged'], weights=[40, 60])[0]

    emit(f"INSERT INTO triage (id, patient_amka, nurse_amka, arrival_time, symptoms, "
         f"urgency_level, outcome, service_time) VALUES ("
         f"{triage_id}, {sql_str(patient['amka'])}, "
         f"{sql_str(random.choice(er_nurses)['amka'])}, "
         f"{sql_datetime(arrival)}, 'Symptoms recorded at triage', "
         f"{urgency}, {sql_str(outcome)}, {sql_datetime(service_time)});")
    triage_records.append({
        'id': triage_id, 'patient_amka': patient['amka'],
        'outcome': outcome, 'arrival': arrival,
    })
    triage_id += 1
emit()

# ============================================================
# 9. HOSPITALIZATIONS
# Q01:  spread across 2 years, all KEN codes, all insurance types
# Q03:  5 patients * 4 stays each in same dept (first 5 patients)
# Q06:  first patient also gets 4 stays -> good target for Q06
# Q09:  3 patient pairs each with total_days = 16 in 2024
# Q14:  3 ICD-10 categories with exactly 5 admissions in 2023 AND 2024
# ============================================================

emit("-- Hospitalizations")
hosp_records = []
hosp_id      = 1

def insert_hosp(patient_amka, dept_id, adm_date, los, icd_adm, icd_dis, triage_ref=None):
    global hosp_id
    bed       = random.choice([b for b in beds if b['dept_id'] == dept_id] or beds[:5])
    ken       = random.choice(KEN_CODES)
    disc_date = min(adm_date + timedelta(days=los), date(2025, 6, 30))
    surcharge = round(
        max(0, los - float(ken[2])) * round(float(ken[1]) / float(ken[2]), 2), 2
    )
    emit(f"INSERT INTO hospitalization "
         f"(id, patient_amka, bed_id, department_id, triage_id, "
         f"admission_date, discharge_date, admission_icd10, discharge_icd10, "
         f"ken_code) VALUES ("
         f"{hosp_id}, {sql_str(patient_amka)}, {bed['id']}, {dept_id}, "
         f"{'NULL' if triage_ref is None else triage_ref}, "
         f"{sql_date(adm_date)}, {sql_date(disc_date)}, "
         f"{sql_str(icd_adm)}, {sql_str(icd_dis)}, "
         f"{sql_str(ken[0])});")
    hosp_records.append({
        'id': hosp_id, 'patient_amka': patient_amka,
        'dept_id': dept_id, 'adm_date': adm_date, 'disc_date': disc_date,
    })
    hosp_id += 1

# --- Q03: 5 patients * 4 stays in same dept ---
q03_patients = patients[:5]
for p in q03_patients:
    dept_id = random.randint(1, 5)
    for _ in range(4):
        adm = random_date(date(2023, 1, 1), date(2024, 6, 1))
        insert_hosp(p['amka'], dept_id, adm, random.randint(3, 10),
                    random.choice(ICD10_CODES), random.choice(ICD10_CODES))

# --- Q09: 3 patient pairs, each pair has total_days=16 in 2024 ---
q09_pairs = [(patients[5], patients[6]),
             (patients[7], patients[8]),
             (patients[9], patients[10])]
for p1, p2 in q09_pairs:
    for p in [p1, p2]:
        adm = random_date(date(2024, 1, 1), date(2024, 6, 1))
        insert_hosp(p['amka'], random.randint(1, NUM_DEPTS), adm, 16,
                    random.choice(ICD10_CODES), random.choice(ICD10_CODES))

# --- Q14: 3 ICD-10 categories * 5 admissions * 2 years = 30 extra hosps ---
q14_categories = list(ICD10_BY_CATEGORY.keys())[:3]
for cat in q14_categories:
    code = ICD10_BY_CATEGORY[cat][0]
    for yr in [2023, 2024]:
        for _ in range(5):
            adm = random_date(date(yr, 1, 1), date(yr, 11, 30))
            insert_hosp(random.choice(patients)['amka'],
                        random.randint(1, NUM_DEPTS), adm,
                        random.randint(2, 8), code, random.choice(ICD10_CODES))

# --- Remaining hospitalizations (fill to 500 total) ---
admitted_triages = [t for t in triage_records if t['outcome'] == 'Admitted']
admitted_idx     = 0

while hosp_id <= 500:
    patient  = random.choice(patients)
    dept_id  = random.randint(1, NUM_DEPTS)
    adm_date = random_date(date(2023, 1, 1), date(2024, 12, 31))

    triage_ref = None
    if admitted_idx < len(admitted_triages):
        triage_ref = admitted_triages[admitted_idx]['id']
        adm_date   = max(admitted_triages[admitted_idx]['arrival'].date(), date(2023, 1, 1))
        admitted_idx += 1

    los = random.choices(range(1, 20),
                         weights=[5,8,12,15,12,10,8,6,5,4,3,3,2,2,2,1,1,1,1])[0]
    insert_hosp(patient['amka'], dept_id, adm_date, los,
                random.choice(ICD10_CODES), random.choice(ICD10_CODES), triage_ref)
emit()

# ============================================================
# 10. LAB TESTS
# ============================================================

emit("-- Lab Tests")
lt_id = 1
for h in random.sample(hosp_records, min(200, len(hosp_records))):
    los   = max(1, (h['disc_date'] - h['adm_date']).days)
    tdate = h['adm_date'] + timedelta(days=random.randint(0, los))
    emit(f"INSERT INTO lab_test "
         f"(id, hospitalization_id, ordering_doctor_amka, code, test_type, "
         f"test_date, result_text, result_value, result_unit, cost) VALUES ("
         f"{lt_id}, {h['id']}, {sql_str(random.choice(doctors)['amka'])}, "
         f"{sql_str(f'LAB{random.randint(1000,9999)}')}, "
         f"{sql_str(random.choice(['Haematological','Biochemical','Imaging','Microbiological']))}, "
         f"{sql_date(tdate)}, 'Result within normal range', "
         f"{round(random.uniform(0.1,999.9),2)}, "
         f"{sql_str(random.choice(['mg/dL','mmol/L','U/L','g/L','%']))}, "
         f"{round(random.uniform(20,300),2)});")
    lt_id += 1
emit()

# ============================================================
# 11. MEDICAL PROCEDURES
# Q02:  procedures in 2025 for shift-year check
# Q05:  young doctors get procedures in 2025
# Q11:  doctors[0] gets 20 procedures; all others get fewer
# ============================================================

emit("-- Medical Procedures")
proc_id      = 1
room_sched   = {r: [] for r in op_rooms}
doc_sched    = {}

def slot_free(schedule, key, s, e):
    return all(e <= a or s >= b for a, b in schedule.get(key, []))

def book_slot(schedule, key, s, e):
    schedule.setdefault(key, []).append((s, e))

def try_insert_proc(surgeon_amka, hosp_id_ref, year=None):
    """Try to schedule one procedure for surgeon in given year. Returns True on success."""
    global proc_id
    yr  = year or random.randint(2023, 2024)
    dt  = datetime(yr, random.randint(1, 11), random.randint(1, 28),
                   random.randint(8, 15))
    dur = random.randint(30, 180)
    end = dt + timedelta(minutes=dur)

    room = next((r for r in random.sample(op_rooms, len(op_rooms))
                 if slot_free(room_sched, r, dt, end)), None)
    if not room:
        return False
    if not slot_free(doc_sched, surgeon_amka, dt, end):
        return False

    book_slot(room_sched, room, dt, end)
    book_slot(doc_sched, surgeon_amka, dt, end)

    emit(f"INSERT INTO medical_procedure "
         f"(id, catalog_code, hospitalization_id, start_datetime, "
         f"duration_minutes, cost, operating_room_id, primary_surgeon_amka) VALUES ("
         f"{proc_id}, {sql_str(random.choice(PROCEDURE_CATALOG_CODES))}, "
         f"{hosp_id_ref}, {sql_datetime(dt)}, {dur}, "
         f"{round(random.uniform(500,8000),2)}, {room}, "
         f"{sql_str(surgeon_amka)});")
    # assistants
    pool = [d['amka'] for d in doctors + nurses if d['amka'] != surgeon_amka]
    for asst in random.sample(pool, min(2, len(pool))):
        emit(f"INSERT IGNORE INTO procedure_staff (procedure_id, staff_amka, role) "
             f"VALUES ({proc_id}, {sql_str(asst)}, 'Assistant');")
    proc_id += 1
    return True

# Q11: top surgeon gets exactly 20 procedures in 2025
top_surgeon = doctors[0]
for _ in range(25):   # attempt 25 times, expect ~20 successes
    try_insert_proc(top_surgeon['amka'], random.choice(hosp_records)['id'], year=2025)

# Q05: young doctors get procedures in 2025
young_doctors = [d for d in doctors
                 if date(1991,1,1) <= d['birth'] <= date(1999,12,31)]
for yd in young_doctors:
    for _ in range(random.randint(3, 7)):
        try_insert_proc(yd['amka'], random.choice(hosp_records)['id'], year=2025)

# Remaining random procedures
for h in random.sample(hosp_records, min(100, len(hosp_records))):
    surgeon = random.choice(doctors)
    try_insert_proc(surgeon['amka'], h['id'])
emit()

# ============================================================
# 12. PRESCRIPTIONS
# Q04:  need prescriptions linking doctor->patient->hospitalization
# Q06:  target patient (patients[0]) needs prescriptions + reviews
# Q10:  20 hospitalizations each get 3 drugs -> substance pairs exist
# T5:   never prescribe a drug whose substance a patient is allergic to
# ============================================================

emit("-- Prescriptions")
presc_id      = 1
presc_keys    = set()
presc_records = []

dosage_opts = ['1 tablet','2 tablets','500mg','250mg','10mg','20mg']
freq_opts   = ['Once daily','Twice daily','Three times daily','Every 8 hours']

def safe_drug(patient_amka):
    """Return a drug_id with no allergy conflict, or None."""
    allergies = allergy_map.get(patient_amka, set())
    if not allergies:
        return random.choice(DRUGS)
    for _ in range(100):
        d = random.choice(DRUGS)
        if not allergies.intersection(drug_to_substances.get(d, set())):
            return d
    return None

def emit_presc(hosp_id_ref, patient_amka, doctor_amka, drug_id, start):
    global presc_id
    key = (doctor_amka, patient_amka, drug_id, start)
    if key in presc_keys:
        return False
    presc_keys.add(key)
    end = start + timedelta(days=random.randint(3, 14))
    emit(f"INSERT INTO prescription "
         f"(id, hospitalization_id, doctor_amka, patient_amka, drug_id, "
         f"start_date, end_date, dosage, frequency) VALUES ("
         f"{presc_id}, {hosp_id_ref}, {sql_str(doctor_amka)}, "
         f"{sql_str(patient_amka)}, {drug_id}, "
         f"{sql_date(start)}, {sql_date(end)}, "
         f"{sql_str(random.choice(dosage_opts))}, "
         f"{sql_str(random.choice(freq_opts))});")
    presc_records.append({
        'hospitalization_id': hosp_id_ref,
        'doctor_amka': doctor_amka,
        'patient_amka': patient_amka,
    })
    presc_id += 1
    return True

# Q10: 20 hospitalizations * 3 distinct drugs each
q10_hosps = random.sample(
    [h for h in hosp_records if h['patient_amka'] not in allergy_amkas],
    min(20, len(hosp_records))
)
for h in q10_hosps:
    used_drugs = set()
    attempts   = 0
    inserted   = 0
    while inserted < 3 and attempts < 50:
        attempts += 1
        drug_id = random.choice(DRUGS)
        if drug_id in used_drugs:
            continue
        doc   = random.choice(doctors)
        start = h['adm_date'] + timedelta(days=random.randint(0, 1))
        if emit_presc(h['id'], h['patient_amka'], doc['amka'], drug_id, start):
            used_drugs.add(drug_id)
            inserted += 1

# Remaining prescriptions for non-allergy patients
safe_hosps = [h for h in hosp_records if h['patient_amka'] not in allergy_amkas]
for h in random.sample(safe_hosps, min(280, len(safe_hosps))):
    drug_id = safe_drug(h['patient_amka'])
    if drug_id is None:
        continue
    doc   = random.choice(doctors)
    start = h['adm_date'] + timedelta(days=random.randint(0, 2))
    emit_presc(h['id'], h['patient_amka'], doc['amka'], drug_id, start)
emit()

# ============================================================
# 13. PATIENT REVIEWS
# Q04:  doctor reviews linked via prescriptions (T10)
# Q06:  target patient gets reviews
# ============================================================

emit("-- Patient Reviews")
rev_hosp_id = 1
rev_doc_id  = 1

hosp_prescribers = {}
for pr in presc_records:
    hosp_prescribers.setdefault(pr['hospitalization_id'], set()).add(pr['doctor_amka'])

completed = [h for h in hosp_records if h['disc_date'] is not None]

for h in random.sample(completed, min(200, len(completed))):
    review_date = h['disc_date'] + timedelta(days=random.randint(1, 30))

    # Hospitalization review (T9 satisfied: discharge_date is always set above)
    emit(f"INSERT IGNORE INTO patient_review_hospitalization "
         f"(id, hospitalization_id, patient_amka, nursing_care, cleanliness, "
         f"food, overall_experience, review_date) VALUES ("
         f"{rev_hosp_id}, {h['id']}, {sql_str(h['patient_amka'])}, "
         f"{random.randint(1,5)}, {random.randint(1,5)}, "
         f"{random.randint(1,5)}, {random.randint(1,5)}, "
         f"{sql_date(review_date)});")
    rev_hosp_id += 1

    # Doctor review (T10: only doctors who prescribed in this hospitalization)
    prescribers = list(hosp_prescribers.get(h['id'], []))
    if not prescribers:
        continue
    emit(f"INSERT IGNORE INTO patient_review_doctor "
         f"(id, hospitalization_id, patient_amka, doctor_amka, medical_care, review_date) "
         f"VALUES ({rev_doc_id}, {h['id']}, {sql_str(h['patient_amka'])}, "
         f"{sql_str(random.choice(prescribers))}, "
         f"{random.randint(1,5)}, {sql_date(review_date)});")
    rev_doc_id += 1
emit()

# ============================================================
# DONE
# ============================================================

emit("SET FOREIGN_KEY_CHECKS = 1;")
emit()
emit("-- ============================================================")
emit("-- Data generation complete")
emit(f"-- Departments:         {NUM_DEPTS}")
emit(f"-- Doctors:             {len(doctors)}  (young: {young_count})")
emit(f"-- Nurses:              120")
emit(f"-- Admin:               60")
emit(f"-- Patients:            200  (allergy: 40)")
emit(f"-- Beds:                {bed_id - 1}")
emit(f"-- Operating rooms:     10")
emit(f"-- Shifts:              {shift_id - 1}")
emit(f"-- Triage:              600")
emit(f"-- Hospitalizations:    {hosp_id - 1}")
emit(f"-- Lab tests:           ~200")
emit(f"-- Procedures:          {proc_id - 1}")
emit(f"-- Prescriptions:       {presc_id - 1}")
emit(f"-- Hosp reviews:        {rev_hosp_id - 1}")
emit(f"-- Doctor reviews:      {rev_doc_id - 1}")
emit("--")
emit("-- Query guarantees:")
emit("-- Q03: 5 patients * 4 stays in same dept")
emit("-- Q05: 10 young doctors (born 1991-99) with procedures in 2025")
emit("-- Q09: 3 patient pairs with identical total days (16) in 2024")
emit("-- Q10: 20 hosps each with 3 co-prescribed drugs")
emit(f"-- Q11: {doctors[0]['amka']} (doctors[0]) has 20 procedures in 2025")
emit("-- Q13: all Registrar_A supervised by Director -> 4-level chains")
emit("-- Q14: 3 ICD-10 categories with exactly 5 admissions in 2023 AND 2024")
emit("-- Q15: 600 triage records, controlled distribution across levels 1-5")
emit("-- ============================================================")

output_path = "./init/generated_data.sql"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"Done. Written to {output_path}", file=sys.stderr)