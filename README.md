# Student Management System

A Django and MySQL application with an HTML, CSS, and JavaScript frontend. It supports student creation, viewing, editing, deletion, search, sign-in/sign-out, and permission-based actions.

## Live application

[Open Student Management System](https://studentmanagementsystem-ck3k.onrender.com/)

The deployed application runs on Render with an Aiven MySQL database. Sign in with an account created in the cloud application; local development accounts are separate.

## Requirements

The working environment uses Python 3.14.4 on Windows and MySQL Server 8.4.11. Use Python 3.14 and MySQL 8.4 for the closest match. Exact Python package versions, including transitive dependencies, are recorded in `requirements.txt`.

- Install [Python](https://www.python.org/downloads/windows/) with pip and venv support.
- Install [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) 8.4 using its Windows MSI and finish MySQL Configurator. Start its Windows service, use port 3306, and remember the root password.
- No Node.js installation or frontend build step is required.

These instructions are for local development, where `DJANGO_DEBUG=True` is set in the local `.env`. The deployed application must use `DJANGO_DEBUG=False`, a separate secret key, and the cloud database connection settings with TLS certificate verification.

## 1. Copy the project and install Python packages

Copy the source to your new machine, including `backend`, `frontend`, all migration files, `requirements.txt`, `.gitignore`, and `backend/.env.example`. Do not copy `.venv`, `.env`, or Python cache folders. Accounts and student records live in MySQL and are not included in the source; this guide creates an empty installation.

In PowerShell, navigate to your project folder (adjust this example path):

```powershell
cd C:\Projects\StudentManagementSystem
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Use the virtual environment's Python directly; activation and execution-policy changes are unnecessary. Stop and resolve any failed command before continuing.

## 2. Create the MySQL database and application account

Connect as root using the default installation path (adjust it if necessary):

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

Enter your root password at the prompt. At `mysql>`, run the following on the new installation. Replace the password placeholder with a private password before executing the SQL:

```sql
CREATE DATABASE student_management
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'student_app'@'localhost'
IDENTIFIED BY 'REPLACE_WITH_YOUR_APPLICATION_PASSWORD';

GRANT ALL PRIVILEGES ON student_management.*
TO 'student_app'@'localhost';

GRANT ALL PRIVILEGES ON test_student_management.*
TO 'student_app'@'localhost';

EXIT;
```

The second grant permits Django to create and destroy its separate test database. Never store normal application data in `test_student_management`. If the account or database already exists, inspect it rather than dropping it or repeating the creation commands blindly.

Verify the application account:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -h localhost -u student_app -p student_management
```

```sql
SELECT DATABASE(), CURRENT_USER();
EXIT;
```

## 3. Configure the environment

From the project root, copy the example only if `.env` does not already exist:

```powershell
if (-not (Test-Path backend\.env)) {
    Copy-Item backend\.env.example backend\.env
}
```

Edit `backend/.env` in your editor and replace `DB_PASSWORD` with the application account password chosen above. The other defaults are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DB_NAME` | `student_management` | Application database |
| `DB_USER` | `student_app` | Application database account |
| `DB_PASSWORD` | Your private password | Database authentication |
| `DB_HOST` | `localhost` | Local MySQL server |
| `DB_PORT` | `3306` | MySQL TCP port |

Also generate a private Django secret key:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated value into `DJANGO_SECRET_KEY` in `backend/.env`, keeping it quoted. Do not share this value or commit it.

All five database variables and `DJANGO_SECRET_KEY` are required by `backend/config/settings.py`. Keep `.env` private; `.gitignore` excludes it. Existing process environment variables take precedence over values loaded from `.env`.

## 4. Apply migrations and create a login

Run from the project root:

```powershell
.\.venv\Scripts\python.exe backend/manage.py check --database default
.\.venv\Scripts\python.exe backend/manage.py migrate
.\.venv\Scripts\python.exe backend/manage.py createsuperuser
```

Choose your own Django username and password. Django accounts are separate from MySQL accounts. Existing migrations already describe the schema, so do not run `makemigrations` just to install the project.

Migration `0002_student_delete_students` historically replaced the original `students` model table with `Student`. On a fresh database this is fine; on an older database containing records in the original table, review that migration and preserve those records before applying it.

## 5. Start the application

```powershell
.\.venv\Scripts\python.exe backend/manage.py runserver
```

Open [the application](http://localhost:8000/) and sign in with the Django account you created. Use the same hostname throughout your session; `localhost` and `127.0.0.1` have separate browser cookies. Stop the development server with Ctrl+C.

| Page | URL |
| --- | --- |
| Students | `http://localhost:8000/` |
| Login | `http://localhost:8000/login/` |
| Django admin | `http://localhost:8000/admin/` |

Django serves the templates and development static files. Do not open `frontend/index.html` directly or serve it with a separate static server: it requires Django template rendering, session authentication, and CSRF tokens.

## 6. Manage user permissions

In Django admin, create regular users and assign the current singular `student` model permissions:

| Role | Permissions |
| --- | --- |
| Viewer | `view_student` |
| Editor | `view_student`, `change_student` |
| Student manager | `view_student`, `add_student`, `change_student`, `delete_student` |

Regular application users do not require staff or superuser status. Staff status permits entry to the admin site but does not itself grant student permissions. The old plural `students` permissions may remain from the original model; do not use those for the current application.

The interface hides unauthorized actions, while backend views independently enforce permissions. After changing permissions, reload the user's page. A superuser has every action available.

## 7. Run automated tests

From the project root:

```powershell
.\.venv\Scripts\python.exe backend/manage.py test students --noinput
```

The current suite has 15 tests covering CRUD, validation, authentication, authorization, missing records, creation CSRF protection, and page permission values. Django creates and destroys `test_student_management`; the dedicated grant above is necessary. These backend tests do not run JavaScript or verify browser layout.

For a browser smoke test, create a disposable student, edit its status, refresh to confirm persistence, search and view it, then delete it and refresh again. Check a view-only account sees no Add, Edit, or Delete actions.

## API reference

| Method | Endpoint | Permission |
| --- | --- | --- |
| GET | `/api/students/` | `view_student` |
| POST | `/api/students/create/` | `add_student` |
| POST | `/api/students/<id>/update/` | `change_student` |
| POST | `/api/students/<id>/delete/` | `delete_student` |

All API endpoints require an authenticated session. POST requests require a CSRF token. Creation and update accept form data with `student_number`, `full_name`, `email`, `department`, and `is_active` (`true` or `false`). The URL ID is the database primary key, not the student number. List responses contain `students`; create/update responses contain `student`.

## Troubleshooting

- **`mysql` is not recognized:** use the full executable path shown above.
- **Connection refused / MySQL error 2003:** check `Get-Service *mysql*` and that the service is running on the configured port.
- **Access denied / MySQL error 1045:** verify the application username/password and host. The root or Django password is not the application database password.
- **Test database access denied:** apply the grant for `test_student_management.*` as root.
- **Missing `DB_*` setting:** confirm the file is named `.env`, not `.env.txt`, and is inside `backend`.
- **`mysqlclient` installation fails:** verify Python 3.14 and matching interpreter architecture. If pip tries to compile instead of installing a wheel, consult the [driver's installation instructions](https://github.com/PyMySQL/mysqlclient#install) for required native build dependencies.
- **CSRF error / expired session:** reload the Django page, sign in again if needed, and use a consistent hostname.
- **API 403:** confirm the user has the relevant current student permission.
- **API 405:** create/update/delete accept POST; opening them in the address bar sends GET.

## Updating dependencies

Install from `requirements.txt` when setting up a machine. After intentionally changing dependencies in the project's isolated environment, run `pip check` and the test suite, then refresh the snapshot from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.txt
