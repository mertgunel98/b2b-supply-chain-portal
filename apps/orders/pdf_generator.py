import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_company_details(company, role='BUYER'):
    """Extracts and formats complete, robust corporate identity details for PDF rendering."""
    if not company:
        name = "Apex Precision Manufacturing Ltd." if role == 'BUYER' else "Atlas Industrial Components A.S."
        contact = "MERT Günel" if role == 'BUYER' else "Corporate Sales Team"
        tax_id = "TR-8947201948" if role == 'BUYER' else "TR-1102938475"
        email = "procurement@apexprecision.com" if role == 'BUYER' else "sales@atlasindustrial.com.tr"
        phone = "+90 (212) 555-0199" if role == 'BUYER' else "+90 (216) 444-8822"
        address = "Organize Sanayi Bolgesi (OSB), 4. Cadde No:12, Nilufer / Bursa" if role == 'BUYER' else "Dudullu OSB, Imes Sanayi Sitesi E Blok No:8, Umraniye / Istanbul"
    else:
        name = company.name or ("Apex Precision Ltd." if role == 'BUYER' else "Atlas Industrial A.S.")
        if role == 'BUYER':
            contact = "MERT Günel"
        else:
            raw_contact = company.contact_person or "Sales Director"
            if "Mert" in raw_contact or "Guner" in raw_contact or "Güner" in raw_contact:
                contact = "MERT Günel"
            else:
                contact = raw_contact
        tax_id = company.tax_id or f"TR-{abs(hash(name)) % 9000000000 + 1000000000}"
        email = company.email or f"info@{name.lower().replace(' ', '').replace('.', '')[:12]}.com"
        phone = company.phone or "+90 (212) 444-0" + str(abs(hash(name)) % 900 + 100)
        
        # Provide realistic industrial address if empty
        if company.address and len(company.address.strip()) > 5:
            address = company.address
        else:
            if role == 'BUYER':
                address = f"Organize Sanayi Bolgesi (OSB), {abs(hash(name)) % 8 + 1}. Cadde No:{abs(hash(name)) % 40 + 10}, Nilufer / Bursa"
            else:
                address = f"Dudullu OSB, IMES Sanayi Sitesi {chr(65 + abs(hash(name)) % 5)} Blok No:{abs(hash(name)) % 30 + 5}, Umraniye / Istanbul"

    return {
        'name': name,
        'contact': contact,
        'tax_id': tax_id,
        'email': email,
        'phone': phone,
        'address': address
    }


def generate_order_pdf(order):
    """Generates a state-of-the-art professional B2B Purchase Order PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )
    party_title = ParagraphStyle(
        'PartyTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1E3A8A')
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155')
    )
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # 1. Header Section
    doc_type_name = "OFFICIAL PURCHASE ORDER" if order.order_type == 'PURCHASE_ORDER' else "REQUEST FOR QUOTATION"
    story.append(Paragraph(f"<b>{doc_type_name}</b>", title_style))
    story.append(Paragraph(
        f"Order Ref #: <b>{order.order_number}</b> &nbsp;|&nbsp; Issue Date: <b>{order.created_at.strftime('%d.%m.%Y')}</b> &nbsp;|&nbsp; Status: <b>{order.get_status_display()}</b>", 
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=14))

    # 2. Company Identity Resolution
    buyer = get_company_details(order.buyer_company, role='BUYER')
    supplier = get_company_details(order.supplier_company, role='SUPPLIER')

    party_data = [
        [
            Paragraph("<b>ISSUED BY (BUYER / PURCHASER):</b>", party_title),
            Paragraph("<b>SUPPLIER (VENDOR / FULFILLMENT):</b>", party_title)
        ],
        [
            Paragraph(
                f"<font size=10><b>{buyer['name']}</b></font><br/>"
                f"<b>Tax ID / VKN:</b> {buyer['tax_id']}<br/>"
                f"<b>Authorized Contact:</b> {buyer['contact']}<br/>"
                f"<b>Corporate Email:</b> {buyer['email']}<br/>"
                f"<b>Phone:</b> {buyer['phone']}<br/>"
                f"<b>Plant / HQ Address:</b> {buyer['address']}",
                cell_style
            ),
            Paragraph(
                f"<font size=10><b>{supplier['name']}</b></font><br/>"
                f"<b>Tax ID / VKN:</b> {supplier['tax_id']}<br/>"
                f"<b>Account Executive:</b> {supplier['contact']}<br/>"
                f"<b>Sales Email:</b> {supplier['email']}<br/>"
                f"<b>Phone:</b> {supplier['phone']}<br/>"
                f"<b>Facility / Warehouse:</b> {supplier['address']}",
                cell_style
            )
        ]
    ]

    party_table = Table(party_data, colWidths=[270, 270])
    party_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EFF6FF')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#93C5FD')),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 12))

    # 3. Logistics & Terms Bar
    expected_delivery = order.expected_delivery_date.strftime('%d.%m.%Y') if order.expected_delivery_date else "Standard 3 Business Days"
    delivery_terms_html = f"<b>Target Delivery Date:</b> {expected_delivery} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Incoterms:</b> DAP (Delivered at Place) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Payment Terms:</b> Net 30 Days (EFT/Wire)"
    
    terms_table = Table([[Paragraph(delivery_terms_html, cell_style)]], colWidths=[540])
    terms_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(terms_table)
    story.append(Spacer(1, 14))

    # 4. Line Items Table
    table_headers = [
        Paragraph("<b>#</b>", header_cell),
        Paragraph("<b>SKU Code</b>", header_cell),
        Paragraph("<b>Material Description & Specs</b>", header_cell),
        Paragraph("<b>Qty</b>", header_cell),
        Paragraph("<b>Unit</b>", header_cell),
        Paragraph("<b>Agreed Price</b>", header_cell),
        Paragraph("<b>Total ($)</b>", header_cell)
    ]
    table_rows = [table_headers]

    subtotal = float(order.total_amount) if order.total_amount else 0.0

    for idx, item in enumerate(order.items.all(), start=1):
        item_qty = item.quantity_requested
        item_price = float(item.agreed_unit_price)
        item_total = float(item.line_total)

        table_rows.append([
            Paragraph(str(idx), cell_style),
            Paragraph(f"<b>{item.product.sku}</b>", cell_style),
            Paragraph(f"<b>{item.product.name}</b><br/><font size=7 color='#64748B'>Category: {item.product.category.name if item.product.category else 'General'}</font>", cell_style),
            Paragraph(str(item_qty), cell_style),
            Paragraph(item.product.unit or 'Pieces', cell_style),
            Paragraph(f"${item_price:,.2f}", cell_style),
            Paragraph(f"${item_total:,.2f}", cell_bold),
        ])

    items_table = Table(table_rows, colWidths=[24, 75, 215, 45, 50, 65, 66])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # 5. Financial Summary Box (Subtotal + VAT + Grand Total)
    vat_amount = subtotal * 0.20
    grand_total = subtotal + vat_amount

    totals_data = [
        [Paragraph("", cell_style), Paragraph("<b>Subtotal (Net Amount):</b>", cell_style), Paragraph(f"${subtotal:,.2f}", cell_style)],
        [Paragraph("", cell_style), Paragraph("<b>VAT / KDV (20%):</b>", cell_style), Paragraph(f"${vat_amount:,.2f}", cell_style)],
        [Paragraph("", cell_style), Paragraph("<b>Grand Total Payable:</b>", cell_bold), Paragraph(f"<b>${grand_total:,.2f}</b>", cell_bold)]
    ]
    totals_table = Table(totals_data, colWidths=[310, 140, 90])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (1,2), (-1,2), colors.HexColor('#EFF6FF')),
        ('BOX', (1,2), (-1,2), 1, colors.HexColor('#2563EB')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 14))

    # 6. Delivery Instructions & Notes
    delivery_notes = order.notes if (order.notes and len(order.notes.strip()) > 0) else f"Deliver cargo directly to {buyer['name']} central goods receiving dock with delivery note (Irsaliye) attached."
    
    notes_data = [
        [
            Paragraph(f"<b>Delivery Destination & Notes:</b><br/>{delivery_notes}", cell_style)
        ]
    ]
    notes_table = Table(notes_data, colWidths=[540])
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(notes_table)
    story.append(Spacer(1, 16))

    # 7. Signature & Stamp Authorization
    sig_data = [
        [
            Paragraph(f"<b>Authorized Purchaser Signature & Stamp:</b><br/><font size=7 color='#64748B'>{buyer['name']}</font><br/><br/><br/>___________________________________<br/>Date: ________________________", cell_style),
            Paragraph(f"<b>Supplier Confirmation & Acceptance:</b><br/><font size=7 color='#64748B'>{supplier['name']}</font><br/><br/><br/>___________________________________<br/>Date: ________________________", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(sig_table)

    # 8. Document Security Footer
    story.append(Spacer(1, 16))
    story.append(Paragraph("<font color='#94A3B8' size=7.5>This document is generated electronically via the MIS 498 B2B Enterprise Supply Chain & Logistics Management Portal. All terms conform to standard B2B commercial procurement regulations.</font>", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_invoice_pdf(invoice):
    """Generates an official, tax-compliant B2B Corporate Invoice PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#065F46'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )
    party_title = ParagraphStyle(
        'PartyTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#065F46')
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155')
    )
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # 1. Header
    story.append(Paragraph("<b>COMMERCIAL TAX INVOICE</b>", title_style))
    story.append(Paragraph(
        f"Invoice #: <b>{invoice.invoice_number}</b> &nbsp;|&nbsp; PO Reference: <b>{invoice.order.order_number}</b> &nbsp;|&nbsp; Issue Date: <b>{invoice.issue_date.strftime('%d.%m.%Y')}</b> &nbsp;|&nbsp; Due Date: <b>{invoice.due_date.strftime('%d.%m.%Y')}</b>", 
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#059669'), spaceAfter=14))

    # 2. Company Identity Resolution
    buyer = get_company_details(invoice.order.buyer_company, role='BUYER')
    supplier = get_company_details(invoice.order.supplier_company, role='SUPPLIER')

    party_data = [
        [
            Paragraph("<b>BILLED FROM (SUPPLIER / SELLER):</b>", party_title),
            Paragraph("<b>BILLED TO (BUYER / CUSTOMER):</b>", party_title)
        ],
        [
            Paragraph(
                f"<font size=10><b>{supplier['name']}</b></font><br/>"
                f"<b>Tax ID / VKN:</b> {supplier['tax_id']}<br/>"
                f"<b>Finance / Billing:</b> {supplier['contact']}<br/>"
                f"<b>Billing Email:</b> {supplier['email']}<br/>"
                f"<b>Corporate Phone:</b> {supplier['phone']}<br/>"
                f"<b>Registered HQ:</b> {supplier['address']}",
                cell_style
            ),
            Paragraph(
                f"<font size=10><b>{buyer['name']}</b></font><br/>"
                f"<b>Tax ID / VKN:</b> {buyer['tax_id']}<br/>"
                f"<b>Accounting Contact:</b> {buyer['contact']}<br/>"
                f"<b>Accounts Payable:</b> {buyer['email']}<br/>"
                f"<b>Corporate Phone:</b> {buyer['phone']}<br/>"
                f"<b>Billing Address:</b> {buyer['address']}",
                cell_style
            )
        ]
    ]

    party_table = Table(party_data, colWidths=[270, 270])
    party_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ECFDF5')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#A7F3D0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#6EE7B7')),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 14))

    # 3. Line Items
    table_headers = [
        Paragraph("<b>#</b>", header_cell),
        Paragraph("<b>SKU Code</b>", header_cell),
        Paragraph("<b>Product / Material Description</b>", header_cell),
        Paragraph("<b>Quantity</b>", header_cell),
        Paragraph("<b>Unit Price</b>", header_cell),
        Paragraph("<b>Amount ($)</b>", header_cell)
    ]
    table_rows = [table_headers]

    for idx, item in enumerate(invoice.order.items.all(), start=1):
        table_rows.append([
            Paragraph(str(idx), cell_style),
            Paragraph(item.product.sku, cell_style),
            Paragraph(f"<b>{item.product.name}</b>", cell_style),
            Paragraph(f"{item.quantity_requested} {item.product.unit}", cell_style),
            Paragraph(f"${float(item.agreed_unit_price):,.2f}", cell_style),
            Paragraph(f"${float(item.line_total):,.2f}", cell_bold),
        ])

    items_table = Table(table_rows, colWidths=[25, 75, 230, 70, 70, 70])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#064E3B')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # 4. Summary Totals
    subtotal = float(invoice.subtotal)
    tax_amt = float(invoice.tax_amount)
    total_due = float(invoice.grand_total)

    totals_data = [
        [Paragraph("", cell_style), Paragraph("<b>Subtotal (Net):</b>", cell_style), Paragraph(f"${subtotal:,.2f}", cell_style)],
        [Paragraph("", cell_style), Paragraph(f"<b>VAT ({invoice.tax_rate:.0f}%):</b>", cell_style), Paragraph(f"${tax_amt:,.2f}", cell_style)],
        [Paragraph("", cell_style), Paragraph("<b>Total Amount Due:</b>", cell_bold), Paragraph(f"<b>${total_due:,.2f}</b>", cell_bold)]
    ]
    totals_table = Table(totals_data, colWidths=[310, 140, 90])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (1,2), (-1,2), colors.HexColor('#ECFDF5')),
        ('BOX', (1,2), (-1,2), 1, colors.HexColor('#059669')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 14))

    # 5. Payment Details
    bank_info = (
        f"<b>Payment Settlement Instructions:</b><br/>"
        f"Bank: <b>Turkiye Is Bankasi A.S. - Kurumsal Ticari Sube</b> &nbsp;|&nbsp; "
        f"IBAN: <b>TR92 0006 4000 0011 2233 4455 66</b> &nbsp;|&nbsp; "
        f"SWIFT / BIC: <b>ISBKTRIS</b><br/>"
        f"Payment Reference: <b>{invoice.invoice_number} / {invoice.order.order_number}</b>"
    )
    bank_table = Table([[Paragraph(bank_info, cell_style)]], colWidths=[540])
    bank_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(bank_table)
    story.append(Spacer(1, 16))

    # 6. Signature
    sig_data = [
        [
            Paragraph(f"<b>Issued By (Finance Department):</b><br/><b>{supplier['name']}</b><br/><br/><br/>___________________________________<br/>Official Signature & Stamp", cell_style),
            Paragraph(f"<b>Received & Accepted By (Purchaser):</b><br/><b>{buyer['name']}</b><br/><br/><br/>___________________________________<br/>Authorized Signature", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph("<font color='#94A3B8' size=7.5>Official electronic commercial invoice issued under the MIS 498 B2B Supply Chain & Automated Logistics Tracking System.</font>", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
