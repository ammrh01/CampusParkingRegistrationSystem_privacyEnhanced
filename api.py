import sqlite3
import csv
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_FILE = 'campus_parking.db'
CSV_FILE = 'raw_parking_data.csv'

# Secret key used strictly for deterministic tokenization of direct identifiers
TOKEN_SALT = b"iium_parking_secure_salt_2026"

def generate_pseudonym(raw_identifier):
    """Converts a direct identifier into a secure, unlinkable pseudonym via HMAC-SHA256."""
    if not raw_identifier:
        return None
    return hmac.new(TOKEN_SALT, str(raw_identifier).strip().encode('utf-8'), hashlib.sha256).hexdigest()

def transform_license_plate(plate):
    """Applies structural character masking to drop exact tracking suffixes."""
    if not plate:
        return "UNKNOWN"
    clean_plate = str(plate).replace(" ", "").upper()
    if len(clean_plate) > 3:
        return f"{clean_plate[:3]}***"
    return "***"

def generalise_vehicle(model):
    """Suppresses fine-grained model metrics into generalized structural categories."""
    if not model:
        return "Other"
    m = str(model).lower()
    if any(x in m for x in ['myvi', 'axia', 'yaris', 'mazda 3', 'swift']):
        return "Hatchback"
    if any(x in m for x in ['saga', 'bezza', 'persona', 'city', 'vios', 'civic', 'almera']):
        return "Sedan"
    if any(x in m for x in ['x50', 'x70', 'crv', 'hrv', 'ativa']):
        return "SUV"
    return "Sedan"

def cluster_faculty(faculty):
    """Aggregates distinct regional faculties into broad administrative clusters."""
    if not faculty:
        return "General"
    f = str(faculty).upper().strip()
    if f in ['KICT', 'KOE']:
        return "STEM_CLUSTER"
    if f in ['KIRKHS', 'KENMS', 'AIKOL']:
        return "HUMANITIES_CLUSTER"
    return "CENTRAL_ADMIN"

def microaggregate_hours(hours):
    """Quantizes exact historical operational intervals into aggregated macro blocks."""
    try:
        val = int(hours)
        if val < 15: return "0-15_LOW"
        if val < 30: return "16-30_MED"
        if val < 45: return "31-45_HIGH"
        return "46+_PEAK"
    except (ValueError, TypeError):
        return "UNKNOWN"

def enforce_retention_policy():
    """Programmatic retention control executing automated destruction of records exceeding TTL."""
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    current_year = datetime.now().year
    retention_threshold = 1  # 1-Year Retention Policy limit for student parking permits
    cutoff_year = current_year - retention_threshold
    
    # Securely purge historical data subject files exceeding policy lifecycle parameters
    cursor.execute("DELETE FROM permits WHERE general_reg_year < ?", (str(cutoff_year),))
    connection.commit()
    connection.close()

def setup_and_populate_db():
    """Initializes schema and runs transformations on raw data assets."""
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    # Schema redesigned around Privacy by Design parameters
    cursor.execute('''CREATE TABLE IF NOT EXISTS permits 
                     (masked_name TEXT, 
                      tokenized_matric TEXT, 
                      masked_plate TEXT, 
                      general_vehicle TEXT,
                      general_reg_year TEXT,
                      clustered_faculty TEXT,
                      aggregated_hours TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM permits")
    if cursor.fetchone()[0] == 0:
        try:
            with open(CSV_FILE, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Apply Privacy-Enhancing Technologies inline during schema ingestion
                    cursor.execute('''INSERT INTO permits VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                 ("REDACTED", 
                                  generate_pseudonym(row['student_name']), 
                                  transform_license_plate(row['license_plate']), 
                                  generalise_vehicle(row['vehicle_model']),
                                  str(row['registration_date'])[:4], # Extract coarse year metrics
                                  cluster_faculty(row['faculty']),
                                  microaggregate_hours(row['monthly_parking_hours'])))
            print("[Privacy Engine] Structural anonymisation and database initialization complete.")
        except FileNotFoundError:
            print(f"[Warning] Source file {CSV_FILE} missing.")
            
    connection.commit()
    connection.close()
    
    # Run lifecycle eviction controls immediately post-initialization
    enforce_retention_policy()

@app.route('/api/register', methods=['POST'])
def register_parking():
    """Data ingress endpoint executing structural minimisation and disassociated transformations."""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid ingress payload"}), 400
        
    # CRITERION 1: Data Minimisation
    # Explicit exclusion of non-essential identifiers (phone_number dropped completely)
    sanitized_payload = {
        "student_name": data.get("student_name"),
        "matric_no": data.get("matric_number"),
        "plate_no": data.get("license_plate"),
        "model": data.get("vehicle_model"),
        "reg_date": data.get("registration_date"),
        "faculty": data.get("faculty"),
        "hours": data.get("monthly_parking_hours")
    }
    
    # CRITERION 2: Disassociated Processing & Inline Transformation
    masked_name = "REDACTED"
    tokenized_matric = generate_pseudonym(sanitized_payload["matric_no"])
    masked_plate = transform_license_plate(sanitized_payload["plate_no"])
    general_vehicle = generalise_vehicle(sanitized_payload["model"])
    
    # Drop fine-grained timestamp attributes into coarse tracking buckets
    raw_date = sanitized_payload["reg_date"] or datetime.now().strftime("%Y-%m-%d")
    general_reg_year = str(raw_date)[:4]
    
    clustered_faculty = cluster_faculty(sanitized_payload["faculty"])
    aggregated_hours = microaggregate_hours(sanitized_payload["hours"])
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO permits VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (masked_name, tokenized_matric, masked_plate, general_vehicle, 
                   general_reg_year, clustered_faculty, aggregated_hours))
    connection.commit()
    connection.close()
    
    # CRITERION 3: Automated Destruction triggering
    enforce_retention_policy()
    
    return jsonify({"status": "success", "message": "Anonymised permit application processed successfully"}), 201

if __name__ == '__main__':
    setup_and_populate_db()
    app.run(port=5000, debug=False)