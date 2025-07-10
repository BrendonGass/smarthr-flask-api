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

# Main endpoint: Get employee by number
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

        # Attempt numeric conversion if employee numbers are stored as integers
        try:
            emp_no_casted = int(emp_no)
        except ValueError:
            emp_no_casted = emp_no  # Keep as string if not a valid number

        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = %s"
        cursor.execute(query, (emp_no_casted,))
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

# Optional: Show the first 10 rows from the table (for debugging)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
