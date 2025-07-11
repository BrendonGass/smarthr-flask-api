
from flask import Flask, request, jsonify
import pymssql

app = Flask(__name__)

DB_CONFIG = {
    "server": "129.232.198.224:51014",
    "user": "SmartHR_Admin",
    "password": "5m@rtHR23!",
    "database": "SmartHR_Demo",
    "timeout": 30
}

def connect_db():
    return pymssql.connect(**DB_CONFIG)

@app.route('/')
def home():
    return "✅ API is running. Use /get-employee or /get-employee-full"

@app.route('/get-employee', methods=['GET'])
def get_employee():
    emp_no = request.args.get('employee_number')
    table = request.args.get('table', 'Personnel')

    if not emp_no:
        return jsonify({"error": "Missing employee_number parameter"}), 400

    if table not in ['Personnel', 'Personnel1']:
        return jsonify({"error": f"Invalid table name: {table}"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor(as_dict=True)
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()
        return jsonify(row if row else {"message": f"No employee found with EmployeeNum {emp_no} in {table}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get-employee-full', methods=['GET'])
def get_employee_full():
    emp_no = request.args.get('employee_number')

    if not emp_no:
        return jsonify({"error": "Missing employee_number parameter"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor(as_dict=True)

        query = '''
        SELECT
            p.EmployeeNum, p.PreferredName, p.Surname, p.Sex, p.EthnicGroup,
            p.Appointdate, p.Appointype, p.JobTitle, p.DeptName,
            p.Termination, p.TerminationDate, p.TerminationReason,
            p1.Position, pl.PositionTitle, pl.Salary,
            pjp.ProfileID, jp.Description, jp.ProfileName,
            pay.PayDate  -- Removed invalid 'Amount' column
        FROM Personnel1 p1
        INNER JOIN PositionLU pl ON p1.Position = pl.Position
        INNER JOIN PositionJobProfiles pjp ON pl.Position = pjp.Position
        INNER JOIN JobProfile jp ON pjp.ProfileID = jp.ID
        INNER JOIN Personnel p ON p1.CompanyNum = p.CompanyNum AND p1.EmployeeNum = p.EmployeeNum
        LEFT JOIN Pay pay ON p.EmployeeNum = pay.EmployeeNum
        WHERE p.EmployeeNum = %s
        '''
        cursor.execute(query, (emp_no,))
        rows = cursor.fetchall()
        return jsonify(rows if rows else {"message": f"No full profile found for EmployeeNum {emp_no}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
