import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# ===== Database Connection Settings =====
DB_USER = "YourID"
DB_PASS = "Password"
DB_DSN  = "acad111"  # TNS alias for Oracle on HarveyV

# ===== Core SQL*Plus Integration =====
def run_sqlplus(sql_block: str) -> str:
    """
    Execute a SQL*Plus session with the provided SQL/PLSQL block and return its output.
    """
    cmd = ['sqlplus', '-s', f"{DB_USER}/{DB_PASS}@{DB_DSN}"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate(sql_block)
    # Filter out prompts and blank lines
    lines = []
    for line in out.splitlines():
        text = line.strip()
        if not text or text.startswith('Connected to') or text.startswith('SQL>'):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def call_procedure(proc_name: str, *args) -> str:
    """
    Build and run a PL/SQL block to invoke a reg_pkg procedure with given arguments.
    """
    quoted = ", ".join(f"'{arg}'" for arg in args)
    sql = (
        "SET SERVEROUTPUT ON\n"
        "SET FEEDBACK OFF\n"
        "SET VERIFY OFF\n"
        "BEGIN\n"
        f"  reg_pkg.{proc_name}({quoted});\n"
        "END;\n"
        "/\n"
        "EXIT;\n"
    )
    return run_sqlplus(sql)

def check_student_exists(bnum: str) -> bool:
    """
    Check if a student with the given B# exists in the database.
    """
    sql = (
        "SET SERVEROUTPUT ON\n"
        "SET FEEDBACK OFF\n"
        "SET VERIFY OFF\n"
        "DECLARE\n"
        "  v_count NUMBER;\n"
        "BEGIN\n"
        f"  SELECT COUNT(*) INTO v_count FROM students WHERE b# = '{bnum}';\n"
        "  IF v_count = 0 THEN\n"
        "    RAISE_APPLICATION_ERROR(-20001, 'Student not found');\n"
        "  END IF;\n"
        "END;\n"
        "/\n"
        "EXIT;\n"
    )
    try:
        run_sqlplus(sql)
        return True
    except:
        return False

# ===== CLI Interface =====
def run_cli():
    menu = [
        "\n===== Main Menu =====",
        "1. Show all students",
        "2. Enroll graduate student in class",
        "3. Drop graduate student from class",
        "4. List students in a class",
        "5. Show all courses",
        "6. Show all classes",
        "7. Delete student",
        "0. Exit"
    ]
    while True:
        print("\n".join(menu))
        choice = input("Enter option number: ").strip()
        if choice == '0':
            print("Exiting.")
            break
        elif choice == '1':
            print(run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_students;\nEXIT;"))
        elif choice == '2':
            b = input("Enter student B#: ").strip()
            c = input("Enter class ID: ").strip()
            out = call_procedure('enroll_grad_student', b, c)
            print("Enrollment succeeded." if 'ORA-' not in out else f"Enrollment failed:\n{out}")
        elif choice == '3':
            b = input("Enter student B#: ").strip()
            c = input("Enter class ID: ").strip()
            out = call_procedure('drop_grad_student', b, c)
            print("Drop succeeded." if 'ORA-' not in out else f"Drop failed:\n{out}")
        elif choice == '4':
            cid = input("Enter class ID: ").strip()
            print(call_procedure('list_students_in_class', cid))
        elif choice == '5':
            print(run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_courses;\nEXIT;"))
        elif choice == '6':
            print(run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_classes;\nEXIT;"))
        elif choice == '7':
            b = input("Enter student B# to delete: ").strip()
            out = call_procedure('delete_student', b)
            print("Deletion succeeded." if 'ORA-' not in out else f"Deletion failed:\n{out}")
        else:
            print("Invalid selection, please try again.")

# ===== Web Interface =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/':
            self.send_html(
                '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Student Management System</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {
                            background-color: #f8f9fa;
                            padding: 20px;
                        }
                        .container {
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }
                        h1 {
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }
                        .menu-list {
                            list-style: none;
                            padding: 0;
                        }
                        .menu-list li {
                            margin: 10px 0;
                        }
                        .menu-list a {
                            display: block;
                            padding: 15px;
                            background: #3498db;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            transition: all 0.3s ease;
                        }
                        .menu-list a:hover {
                            background: #2980b9;
                            transform: translateX(10px);
                        }
                        .back-link {
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }
                        .back-link:hover {
                            color: #2980b9;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Student Management System</h1>
                        <ul class="menu-list">
                            <li><a href="/students">Show All Students</a></li>
                            <li><a href="/enroll">Enroll Graduate Student</a></li>
                            <li><a href="/drop">Drop Graduate Student</a></li>
                            <li><a href="/class">List Students in Class</a></li>
                            <li><a href="/courses">Show All Courses</a></li>
                            <li><a href="/classes">Show All Classes</a></li>
                            <li><a href="/delete">Delete Student</a></li>
                        </ul>
                    </div>
                </body>
                </html>
                '''
            )
        elif path == '/students':
            content = run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_students;\nEXIT;" )
            items = ''.join(f'<li class="list-group-item">{line}</li>' for line in content.splitlines())
            self.send_html(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>All Students</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .list-group {{
                            margin-bottom: 20px;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>All Students</h2>
                        <ul class="list-group">
                            {items}
                        </ul>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            )
        elif path == '/courses':
            content = run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_courses;\nEXIT;" )
            items = ''.join(f'<li class="list-group-item">{line}</li>' for line in content.splitlines())
            self.send_html(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>All Courses</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .list-group {{
                            margin-bottom: 20px;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>All Courses</h2>
                        <ul class="list-group">
                            {items}
                        </ul>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            )
        elif path == '/classes':
            content = run_sqlplus("SET SERVEROUTPUT ON\nEXEC reg_pkg.show_classes;\nEXIT;" )
            items = ''.join(f'<li class="list-group-item">{line}</li>' for line in content.splitlines())
            self.send_html(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>All Classes</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .list-group {{
                            margin-bottom: 20px;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>All Classes</h2>
                        <ul class="list-group">
                            {items}
                        </ul>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            )
        elif path in ['/enroll','/drop','/class','/delete']:
            label = {'/enroll':'Enroll Graduate Student','/drop':'Drop Graduate Student','/class':'List Students in Class','/delete':'Delete Student'}[path]
            form = (
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{label}</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .form-group {{
                            margin-bottom: 20px;
                        }}
                        .form-control {{
                            border-radius: 5px;
                            border: 1px solid #ddd;
                            padding: 10px;
                        }}
                        .btn-primary {{
                            width: 100%;
                            padding: 12px;
                            background: #3498db;
                            border: none;
                            border-radius: 5px;
                            color: white;
                            font-size: 16px;
                            cursor: pointer;
                            transition: background 0.3s ease;
                        }}
                        .btn-primary:hover {{
                            background: #2980b9;
                        }}
                        .back-link {{
                            display: block;
                            text-align: center;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>{label}</h2>
                        <form method="POST">
                '''
            )
            if path in ['/enroll','/drop','/class']:
                form += '''
                            <div class="form-group">
                                <label for="bnum">Student B#:</label>
                                <input type="text" class="form-control" id="bnum" name="bnum" required>
                            </div>
                '''
            if path in ['/enroll','/drop','/class']:
                form += '''
                            <div class="form-group">
                                <label for="classid">Class ID:</label>
                                <input type="text" class="form-control" id="classid" name="classid" required>
                            </div>
                '''
            if path == '/delete':
                form += '''
                            <div class="form-group">
                                <label for="bnum">Student B# to Delete:</label>
                                <input type="text" class="form-control" id="bnum" name="bnum" required>
                            </div>
                            <div class="alert alert-warning">
                                Warning: This action cannot be undone. Please make sure you have the correct student B#.
                            </div>
                '''
            form += '''
                            <button type="submit" class="btn btn-primary">Submit</button>
                        </form>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            self.send_html(form)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        path = self.path
        if path == '/enroll':
            b = params.get('bnum', [''])[0]
            c = params.get('classid', [''])[0]
            out = call_procedure('enroll_grad_student', b, c)
            self.redirect(out)
        elif path == '/drop':
            b = params.get('bnum', [''])[0]
            c = params.get('classid', [''])[0]
            out = call_procedure('drop_grad_student', b, c)
            self.redirect(out)
        elif path == '/class':
            cid = params.get('classid', [''])[0]
            content = call_procedure('list_students_in_class', cid)
            items = ''.join(f'<li class="list-group-item">{line}</li>' for line in content.splitlines())
            self.send_html(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Class Students List</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .list-group {{
                            margin-bottom: 20px;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Students in Class {cid}</h2>
                        <ul class="list-group">
                            {items}
                        </ul>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            )
        elif path == '/delete':
            b = params.get('bnum', [''])[0]
            if not check_student_exists(b):
                self.send_html(
                    f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Error Message</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body {{
                                background-color: #f8f9fa;
                                padding: 20px;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 0 auto;
                                background: white;
                                padding: 30px;
                                border-radius: 10px;
                                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                            }}
                            .error-message {{
                                color: #dc3545;
                                padding: 20px;
                                background: #f8d7da;
                                border-radius: 5px;
                                margin-bottom: 20px;
                            }}
                            .back-link {{
                                display: inline-block;
                                margin-top: 20px;
                                color: #3498db;
                                text-decoration: none;
                            }}
                            .back-link:hover {{
                                color: #2980b9;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="error-message">
                                Error: Student {b} does not exist.
                            </div>
                            <a href="/" class="back-link">Back to Home</a>
                        </div>
                    </body>
                    </html>
                    '''
                )
            else:
                out = call_procedure('delete_student', b)
                if 'ORA-' not in out:
                    self.send_html(
                        f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Delete Success</title>
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                            <style>
                                body {{
                                    background-color: #f8f9fa;
                                    padding: 20px;
                                }}
                                .container {{
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background: white;
                                    padding: 30px;
                                    border-radius: 10px;
                                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                                }}
                                .alert-success {{
                                    padding: 20px;
                                    background: #d4edda;
                                    border-radius: 5px;
                                    margin-bottom: 20px;
                                    color: #155724;
                                }}
                                .back-link {{
                                    display: inline-block;
                                    margin-top: 20px;
                                    color: #3498db;
                                    text-decoration: none;
                                }}
                                .back-link:hover {{
                                    color: #2980b9;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="alert-success">
                                    Student {b} has been successfully deleted.
                                </div>
                                <a href="/" class="back-link">Back to Home</a>
                            </div>
                        </body>
                        </html>
                        '''
                    )
                else:
                    self.redirect(out)
        else:
            self.send_error(404)

    def send_html(self, html: str):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def redirect(self, result: str):
        if 'ORA-' not in result:
            self.send_response(303)
            self.send_header('Location', '/students')
            self.end_headers()
        else:
            safe = result.replace('\n', '<br>')
            self.send_html(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Error Message</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        }}
                        .error-message {{
                            color: #dc3545;
                            padding: 20px;
                            background: #f8d7da;
                            border-radius: 5px;
                            margin-bottom: 20px;
                        }}
                        .back-link {{
                            display: inline-block;
                            margin-top: 20px;
                            color: #3498db;
                            text-decoration: none;
                        }}
                        .back-link:hover {{
                            color: #2980b9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error-message">
                            {safe}
                        </div>
                        <a href="/" class="back-link">Back to Home</a>
                    </div>
                </body>
                </html>
                '''
            )

# ===== Entry point =====
if __name__ == '__main__':
    # Web mode
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        PORT = 8000
        server = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f'Serving on http://localhost:{PORT}  (Ctrl+C to stop)')
        server.serve_forever()
    # CLI mode
    else:
        run_cli()
