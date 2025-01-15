from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_pdf(invoice, doctor, pay_period, billings, facility_fee, gst, deductions, net_payment, filename="receipt.pdf"):
    """
    Generate a PDF receipt for an invoice.

    Args:
        invoice (dict): Details of the invoice.
        doctor (dict): Details of the doctor associated with the invoice.
        pay_period (dict): Payment period details.
        billings (list): List of billing details.
        facility_fee (float): Calculated facility fee.
        gst (float): GST amount.
        deductions (float): Total deductions (facility fee + GST).
        net_payment (float): Net payment amount after deductions.
        filename (str): Name of the PDF file to be generated.
    """
    # Create a PDF document
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    # Title and Header
    content.append(Paragraph("<b>Griffith Medical Centre</b>", styles['Title']))
    content.append(Paragraph("1 Animoo Ave, Griffith NSW 2680, Australia", styles['Normal']))
    content.append(Paragraph("Phone: +61 2 6964 5888", styles['Normal']))
    content.append(Spacer(1, 20))

    # Invoice Details
    content.append(Paragraph("<b>Invoice Details</b>", styles['Heading2']))
    content.append(Paragraph(f"Invoice Number: {invoice['number']}", styles['Normal']))
    content.append(Paragraph(f"Invoice Date Issued: {invoice['date']}", styles['Normal']))
    content.append(Paragraph(f"Payment Period: {pay_period['start']} to {pay_period['end']}", styles['Normal']))
    content.append(Paragraph(f"Doctor: {doctor['name']} (ABN: {doctor['abn']})", styles['Normal']))
    content.append(Spacer(1, 20))

    # Billing Details Table
    content.append(Paragraph("<b>Billing Details</b>", styles['Heading2']))
    table_data = [["Billing Date", "Billing Type", "Billing Ref", "Billing Amount"]]
    for billing in billings:
        table_data.append([billing['date'], billing['type'], billing['ref'], f"${billing['amount']:.2f}"])

    table_data.append(["", "", "Total Billing Amount:", f"${sum(b['amount'] for b in billings):.2f}"])

    table = Table(table_data, colWidths=[100, 150, 150, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)
    content.append(Spacer(1, 20))

    # Payment Summary
    content.append(Paragraph("<b>Discounts and Net Payment</b>", styles['Heading2']))
    content.append(Paragraph(f"Facility Fee: ${facility_fee:.2f}", styles['Normal']))
    content.append(Paragraph(f"GST: ${gst:.2f}", styles['Normal']))
    content.append(Paragraph(f"Total Deductions: ${deductions:.2f}", styles['Normal']))
    content.append(Paragraph(f"<b>Net Payment: ${net_payment:.2f}</b>", styles['Heading3']))
    content.append(Spacer(1, 40))

    # Footer
    content.append(Paragraph("<i>Thank you for your business!</i>", styles['Italic']))
    
    # Build the PDF
    doc.build(content)
