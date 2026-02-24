from flask import Flask, abort, render_template, redirect, request, flash
from dp import db, User, Student, Company, PlacementDrive, Application
from utils.hashing import bcrypt
from utils.auth import login_manager
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from sqlalchemy import or_

app = Flask(__name__, template_folder="templates")
app.secret_key = 'placement-application-portal'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'


with app.app_context():
    db.create_all()
    hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
    if not User.query.filter_by(email="admin@iitm.bs.in").first():
        admin = User(
            email="admin@iitm.bs.in",
            password=hashed_password,
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    return "<button onclick=\"window.location.href='/logout'\">Logout</button>"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect('/dashboard')
        else:
            flash('Invalid email or password')
            return render_template('login.html')
    return render_template('login.html')

def update_status_for_drives(drives):
    today = datetime.today().date()
    for drive in drives:
        if drive.status == "Open" and drive.deadline < today:
            drive.status = "Closed"
        if drive.status == "Closed" and drive.deadline > today:
            drive.status = "Open"
    db.session.commit()

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        return render_template("admin.html")
    elif current_user.role == "student":
        student = Student.query.filter_by(user_id=current_user.id).first()
        applications = student.applications 
        temp = sorted(PlacementDrive.query.filter_by(status="Open").all(), key=lambda d: d.deadline)
        applied_drive_ids = {app.drive_id for app in student.applications}
        drives = [ drive for drive in temp if drive.id not in applied_drive_ids ]
        if not student:
            abort(403)
        return render_template("student_dashboard.html", student=student, drives=drives, applications=applications)
    elif current_user.role == "company":
        company = Company.query.filter_by(user_id=current_user.id).first()
        drives = PlacementDrive.query.filter_by(company_id=company.id).all()
        update_status_for_drives(drives)
        if not company:
            abort(403)
        return render_template("company_dashboard.html", company=company, drives=drives )
    else:
        abort(403)


@app.route("/register/student", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            return render_template(
                "student_register.html",
                error="Email already registered"
            )

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            email=email,
            password=hashed_password,
            role="student",
        )
        db.session.add(user)
        db.session.commit()

        student = Student(
            user_id=user.id,
            name=name
        )
        db.session.add(student)
        db.session.commit()

        return redirect("/login")

    return render_template("student_register.html")

@app.route("/register/company", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        company_name = request.form["company_name"]
        email = request.form["email"]
        password = request.form["password"]
        hr_contact = request.form["hr_contact"]
        website = request.form["website"]

        if User.query.filter_by(email=email).first():
            return render_template(
                "company_register.html",
                error="Email already registered"
            )

        hashed_pw = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            email=email,
            password=hashed_pw,
            role="company",
        )
        db.session.add(user)
        db.session.commit()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            hr_contact=hr_contact,
            website=website,
            blacklisted=False
        )

        db.session.add(company)
        db.session.commit()

        return redirect("/login")

    return render_template("company_register.html")

@app.route("/student/profile/edit", methods=["GET", "POST"])
@login_required
def edit_student_profile():
    if current_user.role != "student":
        abort(403)

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        abort(404)

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()

        duplicate_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if duplicate_user:
            flash("Email already in use.")
            return render_template("student_profile_edit.html", student=student)

        student.name = name
        student.user.email = email
        db.session.commit()
        flash("Profile updated successfully.")
        return redirect("/dashboard")

    return render_template("student_profile_edit.html", student=student)

@app.route("/company/profile/edit", methods=["GET", "POST"])
@login_required
def edit_company_profile():
    if current_user.role != "company":
        abort(403)

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        abort(404)

    if request.method == "POST":
        company_name = request.form["company_name"].strip()
        email = request.form["email"].strip()
        hr_contact = request.form["hr_contact"].strip()
        website = request.form["website"].strip()

        duplicate_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if duplicate_user:
            flash("Email already in use.")
            return render_template("company_profile_edit.html", company=company)

        company.company_name = company_name
        company.user.email = email
        company.hr_contact = hr_contact
        company.website = website
        db.session.commit()
        flash("Profile updated successfully.")
        return redirect("/dashboard")

    return render_template("company_profile_edit.html", company=company)


@app.route("/admin/companies")
@login_required
def admin_companies():
    if current_user.role != "admin":
        abort(403)

    search_query = request.args.get("q", "").strip()
    query = Company.query.join(User, Company.user_id == User.id)

    if search_query:
        filters = [
            Company.company_name.ilike(f"%{search_query}%"),
            User.email.ilike(f"%{search_query}%"),
            Company.hr_contact.ilike(f"%{search_query}%"),
        ]
        if search_query.isdigit():
            filters.append(Company.id == int(search_query))
        query = query.filter(or_(*filters))

    companies = query.order_by(Company.company_name.asc()).all()
    return render_template(
        "admin_company.html",
        companies=companies,
        search_query=search_query
    )

@app.route("/admin/students")
@login_required
def admin_students():
    if current_user.role != "admin":
        abort(403)

    search_query = request.args.get("q", "").strip()
    query = Student.query.join(User, Student.user_id == User.id)

    if search_query:
        filters = [
            Student.name.ilike(f"%{search_query}%"),
            User.email.ilike(f"%{search_query}%"),
        ]
        if search_query.isdigit():
            filters.append(Student.id == int(search_query))
        query = query.filter(or_(*filters))

    students = query.order_by(Student.name.asc()).all()
    return render_template(
        "admin_student.html",
        students=students,
        search_query=search_query
    )

@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
@login_required
def admin_edit_student(student_id):
    if current_user.role != "admin":
        abort(403)

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.")
        return redirect("/admin/students")

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        status = request.form.get("status", student.status)
        blacklisted = request.form.get("blacklisted") == "on"

        duplicate_user = User.query.filter(
            User.email == email,
            User.id != student.user_id
        ).first()
        if duplicate_user:
            flash("Email already in use.")
            return render_template("admin_student_edit.html", student=student)

        student.name = name
        student.user.email = email
        student.blacklisted = blacklisted
        if blacklisted:
            student.status = "Blacklisted"
        else:
            if status == "Blacklisted":
                status = "Pending"
            student.status = status

        db.session.commit()
        flash("Student updated successfully.")
        return redirect("/admin/students")

    return render_template("admin_student_edit.html", student=student)

@app.route("/admin/students/delete/<int:student_id>", methods=["POST"])
@login_required
def admin_delete_student(student_id):
    if current_user.role != "admin":
        abort(403)

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.")
        return redirect("/admin/students")

    user = student.user
    Application.query.filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash("Student deleted successfully.")
    return redirect("/admin/students")

@app.route("/admin/companies/edit/<int:company_id>", methods=["GET", "POST"])
@login_required
def admin_edit_company(company_id):
    if current_user.role != "admin":
        abort(403)

    company = Company.query.get(company_id)
    if not company:
        flash("Company not found.")
        return redirect("/admin/companies")

    if request.method == "POST":
        company_name = request.form["company_name"].strip()
        email = request.form["email"].strip()
        hr_contact = request.form["hr_contact"].strip()
        website = request.form["website"].strip()
        status = request.form.get("status", company.status)
        blacklisted = request.form.get("blacklisted") == "on"

        duplicate_user = User.query.filter(
            User.email == email,
            User.id != company.user_id
        ).first()
        if duplicate_user:
            flash("Email already in use.")
            return render_template("admin_company_edit.html", company=company)

        company.company_name = company_name
        company.user.email = email
        company.hr_contact = hr_contact
        company.website = website
        company.blacklisted = blacklisted
        if blacklisted:
            company.status = "Blacklisted"
        else:
            if status == "Blacklisted":
                status = "Pending"
            company.status = status

        db.session.commit()
        flash("Company updated successfully.")
        return redirect("/admin/companies")

    return render_template("admin_company_edit.html", company=company)

@app.route("/admin/companies/delete/<int:company_id>", methods=["POST"])
@login_required
def admin_delete_company(company_id):
    if current_user.role != "admin":
        abort(403)

    company = Company.query.get(company_id)
    if not company:
        flash("Company not found.")
        return redirect("/admin/companies")

    user = company.user
    for drive in company.drives:
        db.session.delete(drive)

    db.session.delete(company)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash("Company deleted successfully.")
    return redirect("/admin/companies")

@app.route("/admin/drives")
@login_required
def admin_drives():
    if current_user.role != "admin":
        abort(403)

    search_query = request.args.get("q", "").strip()
    query = PlacementDrive.query.join(Company, PlacementDrive.company_id == Company.id)

    if search_query:
        filters = [
            PlacementDrive.job_title.ilike(f"%{search_query}%"),
            Company.company_name.ilike(f"%{search_query}%"),
            PlacementDrive.status.ilike(f"%{search_query}%"),
        ]
        if search_query.isdigit():
            filters.append(PlacementDrive.id == int(search_query))
        query = query.filter(or_(*filters))

    drives = query.order_by(PlacementDrive.deadline.desc()).all()
    update_status_for_drives(drives)
    drives = query.order_by(PlacementDrive.deadline.desc()).all()
    return render_template(
        "admin_drive.html",
        drives=drives,
        search_query=search_query
    )

@app.route("/admin/students/approve/<int:student_id>", methods=["POST"])
@login_required
def activate_student(student_id):
    try:
        if current_user.role != "admin":
            abort(403)

        student = Student.query.get(student_id)

        student.status = "Approved"
        db.session.commit()
        return redirect("/admin/students")
    except Exception:
        flash("An error occurred while activating the student.")
        return redirect("/admin/students")

@app.route("/admin/students/reject/<int:student_id>", methods=["POST"])
@login_required
def reject_student(student_id):
    try:
        if current_user.role != "admin":
            abort(403)

        student = Student.query.get(student_id)
        if not student:
            flash("Student not found.")
            return redirect("/admin/students")

        student.status = "Rejected"
        db.session.commit()
        return redirect("/admin/students")
    except Exception:
        flash("An error occurred while rejecting the student.")
        return redirect("/admin/students")
    
@app.route("/admin/companies/approve/<int:company_id>", methods=["POST"])
@login_required
def activate_company(company_id):
    try:
        if current_user.role != "admin":
            abort(403)

        company = Company.query.get(company_id)

        company.status = "Approved"
        db.session.commit()

        return redirect("/admin/companies")
    except Exception:
        flash("An error occurred while activating the company.")
        return redirect("/admin/companies")

@app.route("/admin/companies/reject/<int:company_id>", methods=["POST"])
@login_required
def reject_company(company_id):
    try:
        if current_user.role != "admin":
            abort(403)

        company = Company.query.get(company_id)
        if not company:
            flash("Company not found.")
            return redirect("/admin/companies")

        company.status = "Rejected"
        db.session.commit()
        return redirect("/admin/companies")
    except Exception:
        flash("An error occurred while rejecting the company.")
        return redirect("/admin/companies")

@app.route("/admin/drives/approve/<int:drive_id>", methods=["POST"])
@login_required
def approve_drive(drive_id):
    try:
        if current_user.role != "admin":
            abort(403)

        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            flash("Drive not found.")
            return redirect("/admin/drives")

        if drive.status == "Pending":
            if drive.deadline and drive.deadline < datetime.today().date():
                drive.status = "Closed"
            else:
                drive.status = "Open"
            db.session.commit()

        return redirect("/admin/drives")
    except Exception:
        flash("An error occurred while approving the drive.")
        return redirect("/admin/drives")

@app.route("/admin/drives/reject/<int:drive_id>", methods=["POST"])
@login_required
def reject_drive(drive_id):
    try:
        if current_user.role != "admin":
            abort(403)

        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            flash("Drive not found.")
            return redirect("/admin/drives")

        drive.status = "Rejected"
        db.session.commit()
        return redirect("/admin/drives")
    except Exception:
        flash("An error occurred while rejecting the drive.")
        return redirect("/admin/drives")

@app.route("/admin/drives/edit/<int:drive_id>", methods=["GET", "POST"])
@login_required
def admin_edit_drive(drive_id):
    if current_user.role != "admin":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        flash("Drive not found.")
        return redirect("/admin/drives")

    if request.method == "POST":
        drive.job_title = request.form["job_title"]
        drive.job_description = request.form["job_description"]
        drive.eligibility = request.form["eligibility"]
        deadline_str = request.form["deadline"]
        drive.deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        if drive.status == "Open" and drive.deadline < datetime.today().date():
            drive.status = "Closed"
        db.session.commit()
        flash("Drive updated successfully.")
        return redirect("/admin/drives")

    return render_template("drive_edit.html", drive=drive)

@app.route("/admin/drives/delete/<int:drive_id>", methods=["POST"])
@login_required
def admin_delete_drive(drive_id):
    if current_user.role != "admin":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        flash("Drive not found.")
        return redirect("/admin/drives")

    db.session.delete(drive)
    db.session.commit()
    flash("Drive deleted successfully.")
    return redirect("/admin/drives")

@app.route("/admin/drives/<int:drive_id>/applications")
@login_required
def admin_view_applications(drive_id):
    if current_user.role != "admin":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        flash("Drive not found.")
        return redirect("/admin/drives")

    applications = drive.applications
    return render_template(
        "applications.html",
        drive=drive,
        applications=applications,
        update_status_url="/admin/applications/update",
        back_url="/admin/drives"
    )

@app.route("/admin/applications/update/<int:application_id>", methods=["POST"])
@login_required
def admin_update_application_status(application_id):
    if current_user.role != "admin":
        abort(403)

    application = Application.query.get(application_id)
    if not application:
        flash("Application not found.")
        abort(404)

    new_status = request.form["status"]
    application.status = new_status
    db.session.commit()

    return redirect(
        f"/admin/drives/{application.drive_id}/applications"
    )

@app.route("/admin/students/blacklist/<int:student_id>", methods=["POST"])
@login_required
def blacklist_student(student_id):
    try:
        if current_user.role != "admin":
            abort(403)

        student = Student.query.get(student_id)

        student.blacklisted = True
        student.status = "Blacklisted"
        db.session.commit()

        return redirect("/admin/students")
    except Exception:
        flash("An error occurred while blacklisting the student.")
        return redirect("/admin/students")
    
@app.route("/admin/companies/blacklist/<int:company_id>", methods=["POST"])
@login_required
def blacklist_company(company_id):
    try:
        if current_user.role != "admin":
            abort(403)

        company = Company.query.get(company_id)

        company.blacklisted = True
        company.status = "Blacklisted"
        db.session.commit()

        return redirect("/admin/companies")
    except Exception:
        flash("An error occurred while blacklisting the company.")
        return redirect("/admin/companies")
    
@app.route("/admin/students/unblacklist/<int:student_id>", methods=["POST"])
@login_required
def unblacklist_student(student_id):
    try:
        if current_user.role != "admin":
            abort(403)

        student = Student.query.get(student_id)

        student.blacklisted = False
        student.status = "Approved"
        db.session.commit()

        return redirect("/admin/students")
    except Exception:
        flash("An error occurred while unblacklisting the student.")
        return redirect("/admin/students")
    
@app.route("/admin/companies/unblacklist/<int:company_id>", methods=["POST"])
@login_required
def unblacklist_company(company_id):
    try:
        if current_user.role != "admin":
            abort(403)

        company = Company.query.get(company_id)

        company.blacklisted = False
        company.status = "Approved"
        db.session.commit()

        return redirect("/admin/companies")
    except Exception:
        flash("An error occurred while unblacklisting the company.")
        return redirect("/admin/companies")
    

@app.route("/company/drives/create", methods=["GET", "POST"])
@login_required
def create_drive():
    try:
        if current_user.role != "company":
            abort(403)

        company = Company.query.filter_by(user_id=current_user.id).first()
        if not company.status == "Approved":
            return "Your account is pending admin approval"
        if company.blacklisted:
            return "Your account is blacklisted. Contact admin for more details."
        
        if request.method == "POST":
            job_title = request.form["job_title"]
            job_description = request.form["job_description"]
            eligibility = request.form["eligibility"]
            deadline_str = request.form["deadline"]

            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

            drive = PlacementDrive(
                company_id=company.id,
                job_title=job_title,
                job_description=job_description,
                eligibility=eligibility,
                deadline=deadline,
                status="Pending"
            )

            db.session.add(drive)
            db.session.commit()
            flash("Drive created and submitted for admin approval.")

            return redirect("/dashboard")
    except Exception:
        flash("An error occurred while creating the drive. Please try again.")

    return render_template("drive.html")



@app.route("/company/drives/<int:drive_id>")
@login_required
def view_drive(drive_id):
    if current_user.role != "company":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)

    company = Company.query.filter_by(user_id=current_user.id).first()
    if drive.company_id != company.id:
        abort(403)

    return render_template(
        "drive_view.html",
        drive=drive
    )

@app.route("/company/drives/edit/<int:drive_id>", methods=["GET", "POST"])
@login_required
def edit_drive(drive_id):
    if current_user.role != "company":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)

    company = Company.query.filter_by(user_id=current_user.id).first()
    if drive.company_id != company.id:
        abort(403)

    if request.method == "POST":
        drive.job_title = request.form["job_title"]
        drive.job_description = request.form["job_description"]
        drive.eligibility = request.form["eligibility"]
        deadline_str = request.form["deadline"]
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        drive.deadline = deadline
        if drive.status == "Open":
            drive.status = "Pending"
            flash("Drive updated. It is now pending admin approval.")
        elif drive.status == "Closed":
            drive.status = "Pending"
            flash("Drive updated. It is now pending admin approval.")

        db.session.commit()
        return redirect("/dashboard")

    return render_template("drive_edit.html", drive=drive)

@app.route("/company/drives/delete/<int:drive_id>", methods=["POST"])
@login_required
def delete_drive(drive_id):
    if current_user.role != "company":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)

    company = Company.query.filter_by(user_id=current_user.id).first()
    if drive.company_id != company.id:
        abort(403)

    db.session.delete(drive)
    db.session.commit()

    return redirect("/dashboard")


@app.route("/student/apply/<int:drive_id>", methods=["POST"])
@login_required
def apply_drive(drive_id):
    if current_user.role != "student":
        abort(403)

    drive = PlacementDrive.query.get(drive_id)
    if drive.status != "Open":
        flash("This drive is closed for applications.")
        return redirect("/dashboard")

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student.status == "Approved":
        flash("Your account is pending admin approval. Cannot apply.")
        return redirect("/dashboard")
    if student.blacklisted:
        flash("Your account is blacklisted. Contact admin for more details. Cannot apply.")
        return redirect("/dashboard")

    existing_application = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing_application:
        flash("You have already applied for this drive.")
        return redirect("/dashboard")

    application = Application(student_id=student.id,drive_id=drive.id)
    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!")
    return redirect("/dashboard")


@app.route("/company/drives/<int:drive_id>/applications")
@login_required
def view_applications(drive_id):
    if current_user.role != "company":
        abort(403)
    try:
        drive = PlacementDrive.query.get(drive_id)
    except:
        flash("Drive not found.")
        abort(404)
    user_id = current_user.id
    company = Company.query.filter_by(user_id=user_id).first()
    if not company:
        abort(403)
    if drive.company_id != company.id:
        abort(403)

    applications = drive.applications
    return render_template(
        "applications.html",
        drive=drive,
        applications=applications,
        update_status_url="/company/applications/update",
        back_url="/dashboard"
    )

@app.route("/company/applications/update/<int:application_id>", methods=["POST"])
@login_required
def update_application_status(application_id):
    if current_user.role != "company":
        abort(403)
    try:
        application = Application.query.get(application_id)
    except:
        flash("Application not found.")
        abort(404)
    user_id = current_user.id
    company = Company.query.filter_by(user_id=user_id).first()
    if not company:
        abort(403)
    if application.drive.company_id != company.id:
        abort(403)

    new_status = request.form["status"]
    application.status = new_status
    db.session.commit()

    return redirect(
        f"/company/drives/{application.drive_id}/applications"
    )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001,debug=True)
