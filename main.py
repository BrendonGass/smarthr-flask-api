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
            conn = pymssql.connect(
                server='129.232.198.224:51014',
                database='SmartHR_Demo',
                user='SmartHR_Admin',
                password='5m@rtHR23!',
                timeout=30
            )
            return conn
        except Exception as e:
            print(f"pymssql connection error: {e}")

    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=129.232.198.224,51014;'
            'DATABASE=SmartHR_Demo;'
            'UID=SmartHR_Admin;'
            'PWD=5m@rtHR23!;'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )
        return conn
    except:
        return pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=129.232.198.224,51014;'
            'DATABASE=SmartHR_Demo;'
            'UID=SmartHR_Admin;'
            'PWD=5m@rtHR23!;'
            'TrustServerCertificate=yes;'
        )

@app.route('/')
def home():
    return "✅ API is running. Try: /get-employee?employee_number=CP003&table=Personnel"

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
        cursor = conn.cursor()
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()

        if row:
            columns = [column[0] for column in cursor.description]
            return jsonify(dict(zip(columns, row)))
        else:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no} in {table}"}), 404

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
        cursor = conn.cursor()

        query = '''
        SELECT 
            p.EmployeeNum, p.PreferredName, p.Surname, p.Sex, p.EthnicGroup, 
            p.Appointdate, p.Appointype, p.JobTitle, p.DeptName, p.Termination, 
            p.TerminationDate, p.TerminationReason, 
            p1.Position, pos.PositionTitle, pos.Salary, 
            pj.ProfileID, j.Description, j.ProfileName,
            pay.Period, pay.PayAmount, pay.PayType
        FROM 
            dbo.Personnel1 p1
            INNER JOIN dbo.PositionLU pos ON p1.Position = pos.Position
            INNER JOIN dbo.PositionJobProfiles pj ON pos.Position = pj.Position
            INNER JOIN dbo.JobProfile j ON pj.ProfileID = j.ID
            INNER JOIN dbo.Personnel p ON p1.CompanyNum = p.CompanyNum AND p1.EmployeeNum = p.EmployeeNum
            LEFT JOIN dbo.Pay pay ON p.EmployeeNum = pay.EmployeeNum
        WHERE 
            p.EmployeeNum = %s
        '''

        cursor.execute(query, (emp_no,))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no}"}), 404

        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
