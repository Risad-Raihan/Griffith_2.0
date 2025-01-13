from app import db
from flask_login import UserMixin
from datetime import datetime


# User Table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Admin' or 'Super Admin'

# Staff Table
class Staff(db.Model):
    EmpID = db.Column(db.Integer, primary_key=True)
    Salutation = db.Column(db.String(50), nullable=True)
    FirstName = db.Column(db.String(150), nullable=False)
    LastName = db.Column(db.String(150), nullable=False)
    Initial = db.Column(db.String(10), nullable=True)
    Address = db.Column(db.String(255), nullable=True)
    City = db.Column(db.String(100), nullable=True)
    State = db.Column(db.String(100), nullable=True)
    Postcode = db.Column(db.String(20), nullable=True)
    Phone = db.Column(db.String(50), nullable=True)
    ABN = db.Column(db.String(50), nullable=True)
    BSB = db.Column(db.String(50), nullable=True)
    ACCT = db.Column(db.String(50), nullable=True)
    FacilityFees_Percent = db.Column(db.Float, nullable=False, default=0.0)
    invoices = db.relationship('Invoice', backref='staff', lazy=True)  # One-to-Many with Invoice

# Invoice Table
class Invoice(db.Model):
    InvID = db.Column(db.Integer, primary_key=True)
    InvNumber = db.Column(db.String(50), unique=True, nullable=False)
    InvDate = db.Column(db.Date, nullable=False)
    RefEmpID = db.Column(db.Integer, db.ForeignKey('staff.EmpID'), nullable=False)  # Foreign Key to Staff
    GrossAmount = db.Column(db.Float, nullable=False)
    FacilityFees = db.Column(db.Float, nullable=True)
    GST = db.Column(db.Float, nullable=True)
    OtherDeduction = db.Column(db.Float, nullable=True)
    NetAmount = db.Column(db.Float, nullable=True)
    PaidOn = db.Column(db.Date, nullable=True)
    RefPeriodSerial = db.Column(db.Integer, db.ForeignKey('pay_period.PeriodSerial'), nullable=True)  # Foreign Key to PayPeriod
    PayType = db.Column(db.String(50), nullable=True)
    billings = db.relationship('Billing', backref='invoice', lazy=True)  # One-to-Many with Billing

# Billing Table
class Billing(db.Model):
    BillingID = db.Column(db.Integer, primary_key=True)
    BillingDate = db.Column(db.Date, nullable=False)
    BillingAmount = db.Column(db.Float, nullable=False)
    BillingType = db.Column(db.String(50), nullable=False)
    BillingRef = db.Column(db.String(100), nullable=True)
    RefInvID = db.Column(db.Integer, db.ForeignKey('invoice.InvID'), nullable=False)  # Foreign Key to Invoice
    Field1 = db.Column(db.String(100), nullable=True)

# PayPeriod Table
class PayPeriod(db.Model):
    PeriodSerial = db.Column(db.Integer, primary_key=True)
    Period_Start_Date = db.Column(db.Date, nullable=False)
    Period_End_Date = db.Column(db.Date, nullable=False)
    invoices = db.relationship('Invoice', backref='pay_period', lazy=True)  # One-to-Many with Invoice


