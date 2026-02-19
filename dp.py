from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    student_profile = db.relationship(
        "Student", backref="user"
    )
    company_profile = db.relationship(
        "Company", backref="user"
    )

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    blacklisted = db.Column(db.Boolean, default=False)
    

class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(150))

    status = db.Column(db.String(20), default="Pending")
    blacklisted = db.Column(db.Boolean, default=False)

class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )

    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.String(2000))
    eligibility = db.Column(db.String(2000))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    drive_id = db.Column(
        db.Integer, db.ForeignKey("placement_drives.id"), nullable=False
    )
    appl_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Applied")

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id"),
    )
