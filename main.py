from flask import Flask, request, jsonify
import pymssql
import pyodbc

app = Flask(__name__)

def connect_db():
    # Try pymssql first
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
        print(f"pymssql failed: {e}")

    # Fall back to pyodbc
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=129.232.198.224,51014;'
            'DATABASE=SmartHR_Demo;'
            'UID=SmartHR_Admin;'
            'PWD=5m@rtHR23!;'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )
        return conn
    except Exception as e2:
        print(f"ODBC connection failed: {e2}")
        raise e2


@app.route('/')
def home():
    return "✅ API is live. Try /get-employee or /get-employee-full"

@app.route('/get-employee', methods=['GET'])
def get_employee():
    emp_no = request.args.get('employee_number')
    table = request.args.get('table', 'Personnel')

    if not emp_no:
        return jsonify({"error": "Missing employee_number"}), 400

    if table not in ['Personnel', 'Personnel1']:
        return jsonify({"error": f"Invalid table name: {table}"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()

        if row:
            columns = [col[0] for col in cursor.description]
            return jsonify(dict(zip(columns, row)))
        else:
            return jsonify({"message": f"No record found for {emp_no} in {table}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
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
        SELECT 
            P.EmployeeNum, P.PreferredName, P.Surname, P.Sex, P.EthnicGroup,
            P.Appointdate, P.Appointype, P.JobTitle, P.DeptName,
            P.Termination, P.TerminationDate, P.TerminationReason,
            P1.Position, LU.PositionTitle, LU.Salary,
            J.ProfileID, JP.ProfileName, JP.Description,
            PAY.PayDate, PAY.Amount, PAY.PayType
        FROM 
            dbo.Personnel P
        LEFT JOIN dbo.Personnel1 P1 ON P.EmployeeNum = P1.EmployeeNum AND P.CompanyNum = P1.CompanyNum
        LEFT JOIN dbo.PositionLU LU ON P1.Position = LU.Position
        LEFT JOIN dbo.PositionJobProfiles J ON LU.Position = J.Position
        LEFT JOIN dbo.JobProfile JP ON J.ProfileID = JP.ID
        LEFT JOIN dbo.Pay PAY ON P.EmployeeNum = PAY.EmployeeNum
        WHERE 
            P.EmployeeNum = %s
        """
        cursor.execute(query, (emp_no,))
        rows = cursor.fetchall()

        if rows:
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            return jsonify(result)
        else:
            return jsonify({"message": f"No full records found for {emp_no}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
