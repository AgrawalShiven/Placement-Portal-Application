from flask import Flask, abort, render_template, redirect, request, flash
from dp import db, User, Student, Company, PlacementDrive, Application
from utils.hashing import bcrypt
from utils.auth import login_manager
from flask_login import login_user, logout_user, login_required, current_user

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

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        return render_template("admin.html")
    elif current_user.role == "student":
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            abort(403)
        return render_template("student_dashboard.html", student=student)
    elif current_user.role == "company":
        company = Company.query.filter_by(user_id=current_user.id).first()
        if not company:
            abort(403)
        return render_template("company_dashboard.html", company=company)
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

        # prevent duplicate email
        if User.query.filter_by(email=email).first():
            return render_template(
                "company_register.html",
                error="Email already registered"
            )

        hashed_pw = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        # create user
        user = User(
            email=email,
            password=hashed_pw,
            role="company",
        )
        db.session.add(user)
        db.session.commit()

        # create company profile (NOT approved yet)
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


@app.route("/admin/companies")
@login_required
def admin_companies():
    if current_user.role != "admin":
        abort(403)

    companies = Company.query.all()
    print("Companies:", companies) 
    return render_template("admin_company.html", companies=companies)

@app.route("/admin/students")
@login_required
def admin_students():
    if current_user.role != "admin":
        abort(403)

    students = Student.query.all()
    return render_template("admin_student.html", students=students)

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
    
if __name__ == '__main__':
    app.run(debug=True)