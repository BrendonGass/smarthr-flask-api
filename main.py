from flask import Flask, request, jsonify
import pymssql

app = Flask(__name__)

# Connect to SQL Server
def connect_db():
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
        print(f"Database connection error: {e}")
        raise e

@app.route('/')
def home():
    return "✅ SmartHR API is running. Try /get-employee?employee_number=0155&table=Personnel"

# Get basic employee data from one table
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

        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = CAST(%s AS NVARCHAR)"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, row))
            return jsonify(result)
        else:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no} in {table}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

# Get full employee info with job profile and pay history
@app.route('/get-full-employee-info', methods=['GET'])
def get_full_employee_info():
    emp_no = request.args.get('employee_number')

    if not emp_no:
        return jsonify({"error": "Missing employee_number parameter"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Query for employee and job info
        query = """
        SELECT
            p.EmployeeNum,
            p.PreferredName,
            p.Surname,
            p.Sex,
            p.EthnicGroup,
            p.Appointdate,
            p.Appointype,
            p.JobTitle,
            p.DeptName,
            p.Termination,
            p.TerminationDate,
            p.TerminationReason,
            p1.Position,
            pos.PositionTitle,
            pos.Salary,
            pjp.ProfileID,
            jp.Description,
            jp.ProfileName
        FROM
            Personnel1 p1
        INNER JOIN PositionLU pos ON p1.Position = pos.Position
        INNER JOIN PositionJobProfiles pjp ON pos.Position = pjp.Position
        INNER JOIN JobProfile jp ON pjp.ProfileID = jp.ID
        INNER JOIN Personnel p ON p1.CompanyNum = p.CompanyNum AND p1.EmployeeNum = p.EmployeeNum
        WHERE
            p.EmployeeNum = CAST(%s AS NVARCHAR)
        """
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no}"}), 404

        columns = [desc[0] for desc in cursor.description]
        employee_info = dict(zip(columns, row))

        # Query for pay history
        cursor.execute("""
            SELECT PayDate, Amount
            FROM Pay
            WHERE EmployeeNum = CAST(%s AS NVARCHAR)
            ORDER BY PayDate DESC
        """, (emp_no,))
        pay_rows = cursor.fetchall()
        pay_history = [{"PayDate": str(r[0]), "Amount": r[1]} for r in pay_rows]

        employee_info["PayHistory"] = pay_history

        return jsonify(employee_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

# Debug route to view 10 sample employee records
@app.route('/debug', methods=['GET'])
def debug():
    table = request.args.get('table', 'Personnel')

    if table not in ['Personnel', 'Personnel1']:
        return jsonify({"error": "Invalid table name"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = f"SELECT TOP 10 * FROM dbo.[{table}]"
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Run locally
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
