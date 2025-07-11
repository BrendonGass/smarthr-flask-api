from flask import Flask, request, jsonify
import pymssql
import pyodbc

app = Flask(__name__)

def connect_db():
    try:
        return pymssql.connect(
            server='129.232.198.224:51014',
            database='SmartHR_Demo',
            user='SmartHR_Admin',
            password='5m@rtHR23!',
            timeout=30
        )
    except Exception:
        return pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=129.232.198.224,51014;'
            'DATABASE=SmartHR_Demo;'
            'UID=SmartHR_Admin;'
            'PWD=5m@rtHR23!;'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )

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
        cursor.execute(f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s", (emp_no,))
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            return jsonify(dict(zip(columns, row)))
        else:
            return jsonify({"message": "Employee not found"}), 404
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

        # Get employee + profile info (1 row)
        cursor.execute("""
            SELECT 
                P.EmployeeNum, P.PreferredName, P.Surname, P.Sex, P.EthnicGroup,
                P.Appointdate, P.Appointype, P.JobTitle, P.DeptName,
                P.Termination, P.TerminationDate, P.TerminationReason,
                P1.Position, LU.PositionTitle, LU.Salary,
                J.ProfileID, JP.ProfileName, JP.Description
            FROM 
                dbo.Personnel P
            LEFT JOIN dbo.Personnel1 P1 ON P.EmployeeNum = P1.EmployeeNum AND P.CompanyNum = P1.CompanyNum
            LEFT JOIN dbo.PositionLU LU ON P1.Position = LU.Position
            LEFT JOIN dbo.PositionJobProfiles J ON LU.Position = J.Position
            LEFT JOIN dbo.JobProfile JP ON J.ProfileID = JP.ID
            WHERE P.EmployeeNum = %s
        """, (emp_no,))
        main_row = cursor.fetchone()
        if not main_row:
            return jsonify({"message": "Employee not found"}), 404
        main_cols = [col[0] for col in cursor.description]
        employee_info = dict(zip(main_cols, main_row))

        # Get pay history (many rows)
        cursor.execute("""
            SELECT PayDate, Amount, PayType
            FROM dbo.Pay
            WHERE EmployeeNum = %s
            ORDER BY PayDate DESC
        """, (emp_no,))
        pay_rows = cursor.fetchall()
        pay_cols = [col[0] for col in cursor.description]
        pay_history = [dict(zip(pay_cols, row)) for row in pay_rows]
        employee_info["PayHistory"] = pay_history

        return jsonify(employee_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
