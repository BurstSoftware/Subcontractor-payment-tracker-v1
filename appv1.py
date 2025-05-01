import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from io import BytesIO

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('subcontractor_payments.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcontractor_name TEXT,
            invoice_number TEXT,
            invoice_amount REAL,
            retainage_percentage REAL,
            retainage_amount REAL,
            payment_status TEXT,
            payment_date TEXT,
            lien_waiver_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Calculate retainage
def calculate_retainage(invoice_amount, retainage_percentage):
    return invoice_amount * (retainage_percentage / 100)

# Save lien waiver file
def save_lien_waiver(uploaded_file):
    if uploaded_file:
        file_path = f"lien_waivers/{uploaded_file.name}"
        os.makedirs('lien_waivers', exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# Add or update payment
def add_payment(subcontractor_name, invoice_number, invoice_amount, retainage_percentage, payment_status, payment_date, lien_waiver_path):
    retainage_amount = calculate_retainage(invoice_amount, retainage_percentage)
    conn = sqlite3.connect('subcontractor_payments.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO payments (subcontractor_name, invoice_number, invoice_amount, retainage_percentage, retainage_amount, payment_status, payment_date, lien_waiver_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (subcontractor_name, invoice_number, invoice_amount, retainage_percentage, retainage_amount, payment_status, payment_date, lien_waiver_path))
    conn.commit()
    conn.close()

# Get all payments
def get_payments():
    conn = sqlite3.connect('subcontractor_payments.db')
    df = pd.read_sql_query("SELECT * FROM payments", conn)
    conn.close()
    return df

# Generate payment history report
def generate_report(df):
    report = df.groupby(['subcontractor_name', 'payment_status']).agg({
        'invoice_amount': 'sum',
        'retainage_amount': 'sum',
        'payment_date': 'count'
    }).reset_index()
    report.columns = ['Subcontractor', 'Status', 'Total Amount', 'Total Retainage', 'Payment Count']
    return report

# Simple Invoice Generator (Placeholder)
def generate_invoice(subcontractor_name, invoice_number, invoice_amount):
    invoice = {
        'subcontractor_name': subcontractor_name,
        'invoice_number': invoice_number,
        'invoice_amount': invoice_amount,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    return invoice

# Streamlit App
st.title("Subcontractor Payment Tracker")

# Initialize database
init_db()

# Sidebar for navigation
menu = st.sidebar.selectbox("Menu", ["Add Payment", "View Payments", "Payment History Report", "Generate Invoice"])

if menu == "Add Payment":
    st.header("Add New Payment")
    with st.form("payment_form"):
        subcontractor_name = st.text_input("Subcontractor Name")
        invoice_number = st.text_input("Invoice Number")
        invoice_amount = st.number_input("Invoice Amount", min_value=0.0, step=100.0)
        retainage_percentage = st.number_input("Retainage Percentage", min_value=0.0, max_value=100.0, value=10.0)
        payment_status = st.selectbox("Payment Status", ["Pending", "Paid"])
        payment_date = st.date_input("Payment Date", datetime.today())
        lien_waiver = st.file_uploader("Upload Lien Waiver", type=['pdf', 'jpg', 'png'])
        submit = st.form_submit_button("Submit")

        if submit:
            lien_waiver_path = save_lien_waiver(lien_waiver)
            add_payment(
                subcontractor_name, invoice_number, invoice_amount, retainage_percentage,
                payment_status, str(payment_date), lien_waiver_path
            )
            st.success("Payment added successfully!")

elif menu == "View Payments":
    st.header("All Payments")
    payments = get_payments()
    if not payments.empty:
        st.dataframe(payments)
        # Download as CSV
        csv = payments.to_csv(index=False).encode('utf-8')
        st.download_button("Download Payments as CSV", csv, "payments.csv", "text/csv")
    else:
        st.info("No payments recorded yet.")

elif menu == "Payment History Report":
    st.header("Payment History Report")
    payments = get_payments()
    if not payments.empty:
        report = generate_report(payments)
        st.dataframe(report)
        # Download report as CSV
        csv = report.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report as CSV", csv, "payment_report.csv", "text/csv")
    else:
        st.info("No data available for report.")

elif menu == "Generate Invoice":
    st.header("Generate Invoice")
    subcontractor_name = st.text_input("Subcontractor Name")
    invoice_number = st.text_input("Invoice Number")
    invoice_amount = st.number_input("Invoice Amount", min_value=0.0, step=100.0)
    if st.button("Generate Invoice"):
        invoice = generate_invoice(subcontractor_name, invoice_number, invoice_amount)
        st.write("### Invoice Details")
        st.json(invoice)
        st.success("Invoice generated! (Placeholder for actual invoice generation)")

# Footer
st.sidebar.markdown("Built with Streamlit | Subcontractor Payment Tracker")
