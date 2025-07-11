from flask import Flask, request, jsonify
import pymssql
from datetime import datetime
from collections import OrderedDict

app = Flask(__name__)

def connect_db():
    return pymssql.connect(
        server='129.232.198.224:51014',
        database='SmartHR_Demo',
        user='SmartHR_Admin',
        password='5m@rtHR23!',
        timeout=30
    )

def derive_pay_period(date_from):
    try:
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, "%Y-%m-%d")
        return date_from.strftime("%B %Y")
    except:
        return None

@app.route('/')
def home():
    return "✅ API is running. Use: /get-employee or /get-employee-full"

@app.route('/get-employee', methods=['GET'])
def get_employee():
    emp_no = request.args.get('employee_number')
    table = request.args.get('table', 'Personnel')
    if not emp_no:
        return jsonify({"error": "Missing employee_number"}), 400
    if table not in ['Personnel', 'Personnel1']:
        return jsonify({"error": f"Invalid table: {table}"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor(as_dict=True)
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()
        return jsonify(row if row else {"message": "Not found"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/get-employee-full', methods=['GET'])
def get_employee_full():
    emp_no = request.args.get('employee_number')
    if not emp_no:
        return jsonify({"error": "Missing employee_number"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor(as_dict=True)

        # Base query for core info
        cursor.execute("""
            SELECT 
                p.*, 
                p1.Position, 
                pos.PositionTitle, 
                pos.Salary AS PositionSalary,
                jp.ProfileName, 
                jp.Description AS ProfileDescription
            FROM Personnel p
            LEFT JOIN Personnel1 p1 ON p1.EmployeeNum = p.EmployeeNum AND p1.CompanyNum = p.CompanyNum
            LEFT JOIN PositionLU pos ON p1.Position = pos.Position
            LEFT JOIN PositionJobProfiles pjp ON pos.Position = pjp.Position
            LEFT JOIN JobProfile jp ON pjp.ProfileID = jp.ID
            WHERE p.EmployeeNum = %s
        """, (emp_no,))
        base_data = cursor.fetchone()

        # Pay history
        cursor.execute("SELECT * FROM dbo.Pay WHERE EmployeeNum = %s ORDER BY DateFrom DESC", (emp_no,))
        pay_rows = cursor.fetchall()

        pay_data = []
        for row in pay_rows:
            period = derive_pay_period(row['DateFrom'])
            template = row.get('TemplateName', '')
            cursor.execute("SELECT * FROM dbo.PayTemplates WHERE TemplateName = %s", (template,))
            template_labels = cursor.fetchone()

            pay_entry = OrderedDict()
            pay_entry["PayPeriod"] = period
            pay_entry["TemplateName"] = template

            for i in range(0, 156):
                val_key = f'Val{i}'
                label_key = f'Label{i}'
                value = row.get(val_key)
                label = template_labels.get(label_key) if template_labels else None
                if label and value not in [None, 0, '', 0.0]:
                    pay_entry[label] = value
            pay_data.append(pay_entry)

        return jsonify({
            "Employee": base_data if base_data else {},
            "PayHistory": pay_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
