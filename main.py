
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
    except Exception as e:
        print(f"ODBC Driver 18 error: {e}")
        try:
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=129.232.198.224,51014;'
                'DATABASE=SmartHR_Demo;'
                'UID=SmartHR_Admin;'
                'PWD=5m@rtHR23!;'
                'TrustServerCertificate=yes;'
            )
            return conn
        except Exception as e2:
            print(f"Fallback to Driver 17 failed: {e2}")
            raise e2

@app.route('/')
def home():
    return "✅ API is running. Try /get-employee or /get-employee-full"

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
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = ?"
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
        query = """
            SELECT
                p.EmployeeNum, p.PreferredName, p.Surname, p.Sex, p.EthnicGroup,
                p.Appointdate, p.Appointype, p.JobTitle, p.DeptName,
                p.Termination, p.TerminationDate, p.TerminationReason,
                p1.Position,
                pl.PositionTitle, pl.Salary,
                pjp.ProfileID,
                jp.Description AS ProfileDescription,
                jp.ProfileName,
                pay.Year, pay.Period, pay.GrossIncome, pay.NetPay
            FROM dbo.Personnel p
            LEFT JOIN dbo.Personnel1 p1 ON p.EmployeeNum = p1.EmployeeNum AND p.CompanyNum = p1.CompanyNum
            LEFT JOIN dbo.PositionLU pl ON p1.Position = pl.Position
            LEFT JOIN dbo.PositionJobProfiles pjp ON pl.Position = pjp.Position
            LEFT JOIN dbo.JobProfile jp ON pjp.ProfileID = jp.ID
            LEFT JOIN dbo.Pay pay ON p.EmployeeNum = pay.EmployeeNum
            WHERE p.EmployeeNum = ?
        """
        cursor.execute(query, (emp_no,))
        rows = cursor.fetchall()

        if rows:
            columns = [col[0] for col in cursor.description]
            return jsonify([dict(zip(columns, row)) for row in rows])
        else:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
