from flask import Flask, request, jsonify
import pyodbc
try:
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    PYMSSQL_AVAILABLE = False

app = Flask(__name__)

# Connect to SQL Server
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
        print(f"Database connection error (ODBC 18): {e}")
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
            print(f"All connection methods failed. Last error: {e2}")
            raise e2

# Home test route
@app.route('/')
def home():
    return "✅ SmartHR API is running. Try: /get-employee?employee_number=CP003&table=Personnel"

# Endpoint to fetch employee by EmployeeNum
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

        # Use safe query and treat EmployeeNum as nvarchar
        query = f"SELECT * FROM dbo.[{table}] WHERE EmployeeNum = ?"
        cursor.execute(query, (emp_no,))
        row = cursor.fetchone()

        if row:
            columns = [column[0] for column in cursor.description]
            result = dict(zip(columns, row))
            return jsonify(result)
        else:
            return jsonify({"message": f"No employee found with EmployeeNum {emp_no} in {table}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'conn' in locals():
            conn.close()

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
