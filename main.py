{
  "openapi": "3.1.0",
  "info": {
    "title": "SmartHR API",
    "version": "1.0.0",
    "description": "An API to access employee information from SmartHR's SQL database."
  },
  "servers": [
    {
      "url": "https://smarthr-flask-api.onrender.com"
    }
  ],
  "paths": {
    "/get-employee": {
      "get": {
        "summary": "Get basic employee info by employee number",
        "operationId": "getEmployee",
        "parameters": [
          {
            "name": "employee_number",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            },
            "description": "The EmployeeNum identifier, such as 'CP003' or 'CEO_1'."
          },
          {
            "name": "table",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "enum": ["Personnel", "Personnel1"],
              "default": "Personnel"
            },
            "description": "Which Personnel table to query (Personnel or Personnel1)."
          }
        ],
        "responses": {
          "200": {
            "description": "Employee data retrieved successfully",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "400": {
            "description": "Missing or invalid parameters"
          },
          "404": {
            "description": "Employee not found"
          },
          "500": {
            "description": "Server error"
          }
        }
      }
    },
    "/get-employee-full": {
      "get": {
        "summary": "Get full employee info including profile details",
        "operationId": "getEmployeeFull",
        "parameters": [
          {
            "name": "employee_number",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            },
            "description": "The EmployeeNum identifier, such as 'CP003' or 'CEO_1'."
          }
        ],
        "responses": {
          "200": {
            "description": "Detailed employee data retrieved",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "400": {
            "description": "Missing or invalid parameters"
          },
          "404": {
            "description": "Employee not found"
          },
          "500": {
            "description": "Server error"
          }
        }
      }
    }
  }
}
