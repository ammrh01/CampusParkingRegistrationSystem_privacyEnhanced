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
TOKEN_SALT = b"iium_parking_secure_salt_2026"

def generate_pseudonym(raw_identifier):
    if not raw_identifier:
        return None
    return hmac.new(TOKEN_SALT, str(raw_identifier).strip().encode('utf-8'), hashlib.sha256).hexdigest()

def transform_license_plate(plate):
    if not plate:
        return "UNKNOWN"
    clean_plate = str(plate).replace(" ", "").upper()
    if len(clean_plate) > 3:
        return f"{clean_plate[:3]}***"
    return "***"

def generalise_vehicle(model):
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
    if not faculty:
        return "General"
    f = str(faculty).upper().strip()
    if f in ['KICT', 'KOE']:
        return "STEM"
    if f in ['KIRKHS', 'KENMS', 'AIKOL']:
        return "HUMANITIES"
    return "CENTRAL ADMIN"

def microaggregate_hours(hours):
    try:
        val = int(hours)
        if val < 15: return "0-15"
        if val < 30: return "16-30"
        if val < 45: return "31-45"
        return "46+"
    except (ValueError, TypeError):
        return "UNKNOWN"

def enforce_retention_policy():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    current_year = datetime.now().year
    
    # Restored to the strict 1-year retention threshold
    cutoff_year = current_year - 1
    cursor.execute("DELETE FROM permits WHERE registration_date < ?", (str(cutoff_year),))
    connection.commit()
    connection.close()

def setup_and_populate_db():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS permits 
                     (student_name TEXT, 
                      matric_number TEXT, 
                      phone_number TEXT, 
                      license_plate TEXT, 
                      vehicle_model TEXT,
                      registration_date TEXT,
                      faculty TEXT,
                      monthly_parking_hours TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM permits")
    if cursor.fetchone()[0] == 0:
        try:
            with open(CSV_FILE, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cursor.execute('''INSERT INTO permits VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                                 ("REDACTED", 
                                  generate_pseudonym(row['matric_number']), 
                                  "REDACTED", 
                                  transform_license_plate(row['license_plate']), 
                                  generalise_vehicle(row['vehicle_model']),
                                  str(row['registration_date'])[:4], 
                                  cluster_faculty(row['faculty']),
                                  microaggregate_hours(row['monthly_parking_hours'])))
        except FileNotFoundError:
            print(f"Warning: {CSV_FILE} not found.")
            
    connection.commit()
    connection.close()
    
    # Runs the cleanup script to delete expired records
    enforce_retention_policy()

@app.route('/api/register', methods=['POST'])
def register_parking():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400
        
    masked_name = "REDACTED"
    tokenized_matric = generate_pseudonym(data.get("matric_number"))
    masked_phone = "REDACTED"
    masked_plate = transform_license_plate(data.get("license_plate"))
    general_vehicle = generalise_vehicle(data.get("vehicle_model"))
    
    raw_date = data.get("registration_date") or datetime.now().strftime("%Y-%m-%d")
    general_reg_year = str(raw_date)[:4]
    
    clustered_faculty = cluster_faculty(data.get("faculty"))
    aggregated_hours = microaggregate_hours(data.get("monthly_parking_hours"))
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO permits VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                  (masked_name, tokenized_matric, masked_phone, masked_plate, 
                   general_vehicle, general_reg_year, clustered_faculty, aggregated_hours))
    connection.commit()
    connection.close()
    
    enforce_retention_policy()
    return jsonify({"status": "success", "message": "Permit processed successfully"}), 201

if __name__ == '__main__':
    setup_and_populate_db()
    app.run(port=5000, debug=False)
