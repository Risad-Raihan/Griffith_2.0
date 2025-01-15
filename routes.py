from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, abort
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.models import db, User, Invoice, Billing, PayPeriod, Staff
from app.utils import generate_pdf
from sqlalchemy.exc import IntegrityError
from datetime import date
import os

# Create a Blueprint for organizing routes (like a mini-app within Flask)
main = Blueprint('main', __name__)

# Initialize the LoginManager
login_manager = LoginManager()

@login_manager.unauthorized_handler
def unauthorized():
    # Redirect to the appropriate login page based on the role
    if not current_user.is_authenticated:
        requested_endpoint = request.endpoint
        if requested_endpoint and "super_admin" in requested_endpoint:
            return redirect(url_for("main.super_admin_login"))
        return redirect(url_for("main.admin_login"))
    return redirect(url_for("main.home"))

# Ensure this is called during app initialization
def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = "main.admin_login"

# Home Route: This serves as the landing page for the app
@main.route('/')
def home():
    return render_template('landingpage.html')

# Admin Login Route
@main.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        fixed_username = "admin"
        fixed_password = "admin123"

        if username == fixed_username and password == fixed_password:
            from flask_login import UserMixin
            class AdminUser(UserMixin):
                def __init__(self, username):
                    self.id = 1
                    self.username = username
                    self.role = "Admin"

            admin_user = AdminUser(username)
            login_user(admin_user)
            return redirect(url_for('main.admin_dashboard'))

        flash('Invalid username or password for Admin', 'danger')

    return render_template('admin_login.html')  # Updated template name here


# Super Admin Login Route
@main.route('/super_admin_login', methods=['GET', 'POST'])
def super_admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Define Super Admin credentials
        super_admin_username = "superadmin"
        super_admin_password = "superadmin123"

        if username == super_admin_username and password == super_admin_password:
            from flask_login import UserMixin
            class SuperAdminUser(UserMixin):
                def __init__(self, username):
                    self.id = 2
                    self.username = username
                    self.role = "Super Admin"

            # Log in the Super Admin user
            super_admin_user = SuperAdminUser(username)
            login_user(super_admin_user)
            return redirect(url_for('main.super_admin_dashboard'))

        flash('Invalid username or password for Super Admin', 'danger')

    return render_template('super_admin_login.html')

# Admin Dashboard Route
@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role not in ["Admin", "Super Admin"]:  # Allow both Admin and Super Admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    return render_template('admin_dashboard.html')

# Super Admin Dashboard Route
@main.route('/super_admin_dashboard')
@login_required
def super_admin_dashboard():
    if current_user.role != "Super Admin":  # Ensure only Super Admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    return render_template('super_admin_dashboard.html')

# Route to Create an Invoice
@main.route('/create_invoice', methods=['GET', 'POST'])
@login_required
def create_invoice():
    # Ensure the user has the right role
    if current_user.role not in ["Admin", "Super Admin"]:  # Allow both Admin and Super Admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    try:
        if request.method == 'POST':
            # Get form data
            inv_number = request.form.get('inv_number')
            inv_date = request.form.get('inv_date')
            paid_date = request.form.get('paid_date')
            doctor_id = request.form.get('doctor')
            pay_period_id = request.form.get('pay_period')

            # Validate required fields
            if not inv_number or not doctor_id or not pay_period_id:
                flash("Missing required fields. Please fill out the form completely.", "danger")
                return redirect(url_for('main.create_invoice'))

            # Parse date fields
            inv_date = date.fromisoformat(inv_date) if inv_date else None
            paid_date = date.fromisoformat(paid_date) if paid_date else None

            # Create and save the new invoice
            new_invoice = Invoice(
                InvNumber=inv_number,
                InvDate=inv_date,
                RefEmpID=doctor_id,
                GrossAmount=0.0,
                FacilityFees=None,
                GST=None,
                OtherDeduction=None,
                NetAmount=0.0,
                PaidOn=paid_date,
                RefPeriodSerial=pay_period_id,
                PayType=None
            )
            db.session.add(new_invoice)
            db.session.commit()

            # Redirect to the add billings page after successful invoice creation
            flash('Invoice created successfully!', 'success')
            return redirect(url_for('main.add_billings', invoice_id=new_invoice.InvID))

    except IntegrityError:
        # Handle duplicate invoice number
        db.session.rollback()
        flash('Invoice number already exists. Please use a unique invoice number.', 'danger')

    except Exception as e:
        # Log and flash unexpected errors for debugging
        print(f"Error in create_invoice: {e}")
        flash('An unexpected error occurred. Please try again.', 'danger')

    # For GET requests, render the form
    pay_periods = PayPeriod.query.all()
    doctors = Staff.query.all()

    # Check if required data is missing
    if not pay_periods or not doctors:
        flash("Pay Periods or Doctors data is missing. Please ensure the database is properly populated.", "warning")

    return render_template('create_invoice.html', pay_periods=pay_periods, doctors=doctors)

# Route to Add Billings
@main.route('/add_billings/<int:invoice_id>', methods=['GET', 'POST'])
def add_billings(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    billings = Billing.query.filter_by(RefInvID=invoice_id).all()

    if request.method == 'POST':
        billing_date = request.form.get('billing_date')
        billing_type = request.form.get('billing_type')
        billing_ref = request.form.get('billing_ref')
        billing_amount = request.form.get('billing_amount')

        billing_date = date.fromisoformat(billing_date) if billing_date else None

        new_billing = Billing(
            BillingDate=billing_date,
            BillingType=billing_type,
            BillingRef=billing_ref,
            BillingAmount=float(billing_amount),
            RefInvID=invoice_id
        )
        db.session.add(new_billing)

        invoice.GrossAmount += float(billing_amount)
        db.session.commit()

        flash('Billing added successfully!', 'success')
        return redirect(url_for('main.add_billings', invoice_id=invoice_id))

    return render_template('add_billings.html', invoice=invoice, billings=billings, invoice_id=invoice_id)

# Route to Fetch Doctor Details (AJAX)
@main.route('/get_doctor_details/<int:doctor_id>')
def get_doctor_details(doctor_id):
    doctor = Staff.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    gst = doctor.FacilityFees_Percent * 0.1

    return jsonify({
        'facility_fee': doctor.FacilityFees_Percent,
        'gst': gst
    })

# Route to View Full Receipt
@main.route('/full_receipt/<int:invoice_id>')
def full_receipt(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    doctor = Staff.query.get(invoice.RefEmpID)
    pay_period = PayPeriod.query.get(invoice.RefPeriodSerial)
    billings = Billing.query.filter_by(RefInvID=invoice_id).all()

    total_billing = sum(b.BillingAmount for b in billings)
    facility_fee_percent = doctor.FacilityFees_Percent if doctor else 0.0
    facility_fee_amount = (facility_fee_percent / 100) * total_billing
    gst_amount = invoice.GST if invoice.GST else 0.0
    total_deductions = facility_fee_amount + gst_amount
    net_payment = total_billing - total_deductions

    return render_template(
        'full_receipt.html',
        invoice=invoice,
        doctor=doctor,
        pay_period=pay_period,
        billings=billings,
        total_billing=total_billing,
        facility_fee_amount=facility_fee_amount,
        gst_amount=gst_amount,
        total_deductions=total_deductions,
        net_payment=net_payment,
        invoice_id=invoice_id
    )

# Route to Download Receipt
@main.route('/download_receipt/<int:invoice_id>')
def download_receipt(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    doctor = Staff.query.get(invoice.RefEmpID)
    pay_period = PayPeriod.query.get(invoice.RefPeriodSerial)
    billings = Billing.query.filter_by(RefInvID=invoice_id).all()

    total_billing = sum(b.BillingAmount for b in billings)
    facility_fee_percent = doctor.FacilityFees_Percent if doctor else 0.0
    facility_fee_amount = (facility_fee_percent / 100) * total_billing
    gst_amount = invoice.GST if invoice.GST else 0.0
    total_deductions = facility_fee_amount + gst_amount
    net_payment = total_billing - total_deductions

    # Fix path for the PDF file
    output_dir = os.path.join(os.getcwd(), "app")
    filename = os.path.join(output_dir, f"receipt_{invoice_id}.pdf")

    generate_pdf(
        invoice={
            'number': invoice.InvNumber,
            'date': invoice.InvDate
        },
        doctor={
            'name': f"{doctor.FirstName} {doctor.LastName}",
            'abn': doctor.ABN
        },
        pay_period={
            'start': pay_period.Period_Start_Date,
            'end': pay_period.Period_End_Date
        },
        billings=[
            {
                'date': billing.BillingDate,
                'type': billing.BillingType,
                'ref': billing.BillingRef,
                'amount': billing.BillingAmount
            } for billing in billings
        ],
        facility_fee=facility_fee_amount,
        gst=gst_amount,
        deductions=total_deductions,
        net_payment=net_payment,
        filename=filename
    )

    return send_file(filename, as_attachment=True)

@main.route('/admin/view-receipts')
@login_required
def view_past_receipts():
    if current_user.role not in ["Admin", "Super Admin"]:  # Allow both Admin and Super Admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    invoices = Invoice.query.all()  # Fetch all invoices
    staff = Staff.query.all()  # Fetch all staff members
    billings = Billing.query.all()  # Fetch all billings

    # Group data by invoice ID
    receipts = []
    for invoice in invoices:
        doctor = next((s for s in staff if s.EmpID == invoice.RefEmpID), None)
        invoice_billings = [b for b in billings if b.RefInvID == invoice.InvID]
        receipts.append({
            "invoice": invoice,
            "doctor": doctor,
            "billings": invoice_billings
        })

    return render_template('view_receipts.html', receipts=receipts)

# Route for System Settings
@main.route('/system_settings')
@login_required
def system_settings():
    if current_user.role != "Super Admin":  # Restrict access to Super Admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    return render_template('system_settings.html')


# System Settings: Admins
@main.route('/system_settings/admins')
@login_required
def view_admins():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    admins = User.query.filter_by(role="Admin").all()
    if not admins:
        flash("No data available in the Admins table.", "info")
    return render_template('view_table.html', title="Admins", table_data=admins, getattr=getattr)

# System Settings: Invoices
@main.route('/system_settings/invoices', methods=['GET'])
@login_required
def view_invoices():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    invoices = Invoice.query.all()
    if not invoices:
        flash("No data available in the Invoices table.", "info")
    return render_template(
        'view_table.html',
        title="Invoices",
        table_data=invoices,
        table_name="invoices",  # Pass unique table_name
        getattr=getattr
    )

# System Settings: Billings
@main.route('/system_settings/billings', methods=['GET'])
@login_required
def view_billings():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    billings = Billing.query.all()
    if not billings:
        flash("No data available in the Billings table.", "info")
    return render_template(
        'view_table.html',
        title="Billings",
        table_data=billings,
        table_name="billings",  # Pass unique table_name
        getattr=getattr
    )

# System Settings: Staff
@main.route('/system_settings/staff', methods=['GET'])
@login_required
def view_staff():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    # Query staff data
    staff = Staff.query.all()

    # Fetch column keys dynamically from the Staff model
    column_keys = [col.key for col in Staff.__table__.columns]

    # Debugging: Print the fetched column keys
    print("Fetched Column Keys:", column_keys)

    if not staff:
        flash("No data available in the Staff table.", "info")

    return render_template(
    'view_table.html',
    title="Staff",
    table_data=staff,
    table_name="staff",  # Ensure this matches
    table_columns=column_keys,  # Pass column keys dynamically
    getattr=getattr
)


# System Settings: Pay Periods
@main.route('/system_settings/pay_periods', methods=['GET'])
@login_required
def view_pay_periods():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    pay_periods = PayPeriod.query.all()
    if not pay_periods:
        flash("No data available in the Pay Periods table.", "info")
    return render_template(
        'view_table.html',
        title="Pay Periods",
        table_data=pay_periods,
        table_name="pay_periods",  # Pass unique table_name
        getattr=getattr
    )

from datetime import datetime

@main.route('/system_settings/add_pay_period', methods=['POST'])
@login_required
def add_pay_period():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.system_settings'))

    # Retrieve form data
    start_date = request.form.get('period_start_date')
    end_date = request.form.get('period_end_date')

    if not start_date or not end_date:
        flash("Start Date and End Date are required!", "danger")
        return redirect(url_for('main.view_pay_periods'))

    try:
        # Validate that no overlapping date range exists
        existing_periods = PayPeriod.query.all()
        for period in existing_periods:
            if start_date == str(period.Period_Start_Date) or end_date == str(period.Period_End_Date):
                flash("Pay period with the same date range already exists. Please enter a valid date range.", "danger")
                return redirect(url_for('main.view_pay_periods'))

        # Add the new pay period to the database
        new_serial = db.session.query(PayPeriod).count() + 1  # Auto-increment the serial
        new_pay_period = PayPeriod(
            PeriodSerial=new_serial,
            Period_Start_Date=start_date,
            Period_End_Date=end_date
        )
        db.session.add(new_pay_period)
        db.session.commit()

        # Log success
        print("PayPeriod added to DB:", new_pay_period)
        flash("Pay Period added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding Pay Period to DB: {str(e)}")
        flash(f"Error adding Pay Period: {str(e)}", "danger")

    return redirect(url_for('main.view_pay_periods'))

# Add Staff Entry
@main.route('/system_settings/add_staff', methods=['POST'])
@login_required
def add_staff():
    if current_user.role != "Super Admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.view_staff'))
    
    try:
        # Auto-generate EmpID
        new_emp_id = db.session.query(Staff).count() + 1

        # Dynamically retrieve all form fields
        staff_data = {
            'EmpID': new_emp_id,  # Automatically set EmpID
        }
        # Add all fields except EmpID dynamically
        for column in Staff.__table__.columns.keys():
            if column != 'EmpID':
                staff_data[column] = request.form.get(column.lower())

        # Handle FacilityFees_Percent explicitly as it requires conversion
        if 'FacilityFees_Percent' in staff_data and staff_data['FacilityFees_Percent']:
            staff_data['FacilityFees_Percent'] = float(staff_data['FacilityFees_Percent'])
        else:
            staff_data['FacilityFees_Percent'] = 0.0

        # Create new staff entry
        new_staff = Staff(**staff_data)

        # Save to database
        db.session.add(new_staff)
        db.session.commit()
        flash("Staff added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding Staff: {e}")
        flash("Error adding staff. Please check your input.", "danger")

    return redirect(url_for('main.view_staff'))
