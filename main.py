from flask import Flask, request, jsonify
import pyodbc
try:
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    PYMSSQL_AVAILABLE = False

app = Flask(__name__)

def connect_db():
    if PYMSSQL_AVAILABLE:
        try:
            return pymssql.connect(
                server='129.232.198.224:51014',
                database='SmartHR_Demo',
                user='SmartHR_Admin',
                password='5m@rtHR23!',
                timeout=30
            )
        except Exception as e:
            print(f"pymssql error: {e}")
    try:
        return pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=129.232.198.224,51014;'
            'DATABASE=SmartHR_Demo;'
            'UID=SmartHR_Admin;'
            'PWD=5m@rtHR23!;'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )
    except Exception as e:
        print(f"ODBC Driver 18 failed: {e}")
        try:
            return pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=129.232.198.224,51014;'
                'DATABASE=SmartHR_Demo;'
                'UID=SmartHR_Admin;'
                'PWD=5m@rtHR23!;'
                'TrustServerCertificate=yes;'
            )
        except Exception as e2:
            print(f"ODBC Driver 17 failed: {e2}")
            raise e2

@app.route('/')
def home():
    return "✅ API is live. Try /get-employee, /get-employee-full, or /get-pay-history"

@app.route('/get-employee', methods=['GET'])
def get_employee():
    emp_no = request.args.get('employee_number')
    table = request.args.get('table', 'Personnel')
    if not emp_no:
        return jsonify({"error": "Missing employee_number"}), 400
    if table not in ['Personnel', 'Personnel1']:
        return jsonify({"error": "Invalid table name"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = ?", (emp_no,))
        row = cursor.fetchone()
        if row:
            cols = [col[0] for col in cursor.description]
            return jsonify(dict(zip(cols, row)))
        else:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no} in {table}"}), 404
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
        cursor = conn.cursor()
        query = """
        SELECT Personnel.EmployeeNum, Personnel.PreferredName, Personnel.Surname, Personnel.Sex,
               Personnel.EthnicGroup, Personnel.Appointdate, Personnel.Appointype, Personnel.JobTitle,
               Personnel.DeptName, Personnel.Termination, Personnel.TerminationDate, Personnel.TerminationReason,
               Personnel1.Position, PositionLU.PositionTitle, PositionLU.Salary,
               PositionJobProfiles.ProfileID, JobProfile.Description, JobProfile.ProfileName
        FROM Personnel1
        INNER JOIN PositionLU ON Personnel1.Position = PositionLU.Position
        INNER JOIN PositionJobProfiles ON PositionLU.Position = PositionJobProfiles.Position
        INNER JOIN JobProfile ON PositionJobProfiles.ProfileID = JobProfile.ID
        INNER JOIN Personnel ON Personnel1.CompanyNum = Personnel.CompanyNum AND Personnel1.EmployeeNum = Personnel.EmployeeNum
        WHERE Personnel.EmployeeNum = ?
        """
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()
        if row:
            cols = [col[0] for col in cursor.description]
            return jsonify(dict(zip(cols, row)))
        else:
            return jsonify({"message": f"No data found for {emp_no}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/get-pay-history', methods=['GET'])
def get_pay_history():
    emp_no = request.args.get('employee_number')
    if not emp_no:
        return jsonify({"error": "Missing employee_number"}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.Pay WHERE EmployeeNum = ?", (emp_no,))
        rows = cursor.fetchall()
        if rows:
            cols = [col[0] for col in cursor.description]
            return jsonify([dict(zip(cols, row)) for row in rows])
        else:
            return jsonify({"message": f"No pay history found for {emp_no}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
