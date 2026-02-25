# Placement Portal Application

A role-based placement management web app built with Flask.  
It supports **students**, **companies**, and **admins** with approval workflows, placement drive management, and application tracking.

## Features

### Authentication and Roles
- Login/logout with session management (`Flask-Login`)
- Role-based dashboards for:
  - `admin`
  - `student`
  - `company`
- Password hashing with `Flask-Bcrypt`

### Student Features
- Register and login
- Update own profile (name, email)
- View approved/open drives
- Apply to drives (single application per drive)
- View application history and statuses

### Company Features
- Register and login
- Update own profile (company name, email, HR contact, website)
- Create, edit, delete placement drives
- View applicants for drives
- Update applicant status per drive (`Applied`, `Shortlisted`, `Selected`, `Rejected`)

### Admin Features
- Manage students:
  - Search
  - Approve / reject
  - Blacklist / unblacklist
  - Edit / delete
- Manage companies:
  - Search
  - Approve / reject
  - Blacklist / unblacklist
  - Edit / delete
- Manage drives:
  - Search
  - Approve / reject
  - Edit / delete
  - View applicants and update application statuses

### Approval Workflow
- Newly registered students/companies start as `Pending`
- Newly created drives start as `Pending`
- Admin approval is required before drives are visible to students

## Tech Stack
- Python 3.12+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- SQLite
- Jinja2 templates + Bootstrap 5

## Project Structure

```text
.
├── app.py                       # Main Flask app and routes
├── dp.py                        # SQLAlchemy models
├── utils/
│   ├── auth.py                  # Login manager config
│   └── hashing.py               # Bcrypt config
├── templates/                   # Jinja templates
│   ├── admin*.html              # Admin pages
│   ├── student*.html            # Student pages
│   ├── company*.html            # Company pages
│   ├── drive*.html              # Drive create/edit/view
│   └── applications.html        # Applicant list + status updates
├── instance/
│   └── placement_portal.db      # SQLite DB file
├── pyproject.toml               # Project config + dependencies
└── README.md
```

## Setup

### 1. Clone and enter project
```bash
git clone <your-repo-url>
cd Placement-Portal-Application
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
Using `uv`:
```bash
uv sync
```

Or using `pip`:
```bash
pip install flask flask-bcrypt flask-login flask-sqlalchemy pytz
```

## Run the Application

```bash
python3 app.py
```

The app starts in debug mode by default and creates tables automatically on first run.

## Default Admin Credentials

Created automatically if missing:
- Email: `admin@iitm.bs.in`
- Password: `admin123`

## Database

- DB URI: `sqlite:///placement_portal.db`
- Physical file is under the Flask instance folder: `instance/placement_portal.db`

## Core Data Models

Defined in `dp.py`:
- `User`
- `Student`
- `Company`
- `PlacementDrive`
- `Application`

Important constraints:
- Unique `User.email`
- Unique student application per drive (`student_id`, `drive_id`)

## Common Workflows

### Student
1. Register
2. Wait for admin approval
3. Login and apply to open drives
4. Track status updates

### Company
1. Register
2. Wait for admin approval
3. Create drive (goes to pending)
4. After admin drive approval, receive applications
5. Update applicant statuses

### Admin
1. Approve/reject students and companies
2. Approve/reject drives
3. Edit/delete entities when required
4. Monitor and update applications per drive

## Notes
- Drive status auto-updates based on deadline (`Open` ↔ `Closed` checks in dashboard flow).
- Flash messages are used throughout for user feedback.
- Some account states (e.g., blacklisted) restrict actions.

## Future Improvements
- Add migration support (`Flask-Migrate`/Alembic)
- Add automated tests (unit + integration)
- Add role-based API endpoints
- Improve UI consistency for flash message handling
- Add pagination for admin tables
