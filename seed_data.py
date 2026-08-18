"""
Database Seeder for B2B Supply Chain and Inventory Tracking Portal.
Populates realistic SMEs, Suppliers, 36+ Industrial Products, Stock entries (healthy & critical), Purchase Orders, and Invoices.
"""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from apps.accounts.models import Company, UserProfile
from apps.inventory.models import Category, Product, InventoryItem
from apps.orders.models import PurchaseOrder, OrderItem, Invoice
from apps.scoring.models import ScoringConfiguration
from apps.scoring.algorithm import refresh_all_supplier_evaluations

def run_seed():
    print("[INFO] Starting comprehensive B2B Portal database seeding...")

    # 1. Clean previous data
    Invoice.objects.all().delete()
    OrderItem.objects.all().delete()
    PurchaseOrder.objects.all().delete()
    InventoryItem.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    UserProfile.objects.all().delete()
    Company.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()

    # 2. Create Companies & User Credentials
    sme = Company.objects.create(
        name="Apex Precision Manufacturing Ltd.",
        company_type="SME",
        tax_id="TR-8947201948",
        email="procurement@apexprecision.com",
        phone="+90 (212) 555-0199",
        address="Organize Sanayi Bolgesi, 4. Cadde No:12, Nilufer / Bursa",
        contact_person="MERT Günel"
    )
    user_sme = User.objects.create_user(username="buyer_apex", email="procurement@apexprecision.com", password="password123")
    UserProfile.objects.create(user=user_sme, company=sme, role_title="Head of Supply Chain")

    sup1 = Company.objects.create(
        name="Atlas Industrial Components A.S.",
        company_type="SUPPLIER",
        tax_id="TR-1102938475",
        email="sales@atlasindustrial.com.tr",
        phone="+90 (216) 444-8822",
        address="Dudullu OSB, Imes Sanayi Sitesi E Blok, Umraniye / Istanbul",
        contact_person="Selim Yilmaz (Sales Director)"
    )
    user_sup1 = User.objects.create_user(username="supplier_atlas", email="sales@atlasindustrial.com.tr", password="password123")
    UserProfile.objects.create(user=user_sup1, company=sup1, role_title="Sales & Operations Director")

    sup2 = Company.objects.create(
        name="TeknoSupply Electronics & Hardware",
        company_type="SUPPLIER",
        tax_id="TR-6655443322",
        email="orders@teknosupply.com",
        phone="+90 (232) 321-7788",
        address="Ataturk Organize Sanayi Bolgesi 10024 Sok., Cigli / Izmir",
        contact_person="Ayse Kaya (Key Account Manager)"
    )
    user_sup2 = User.objects.create_user(username="supplier_tekno", email="orders@teknosupply.com", password="password123")
    UserProfile.objects.create(user=user_sup2, company=sup2, role_title="Key Account Manager")

    sup3 = Company.objects.create(
        name="Global Pack & Polymer Materials Co.",
        company_type="SUPPLIER",
        tax_id="TR-9988776655",
        email="b2b@globalpack.com",
        phone="+90 (224) 211-3344",
        address="Demirtas OSB, Gul Sok. No:5, Osmangazi / Bursa",
        contact_person="Emre Can (Logistics Lead)"
    )
    user_sup3 = User.objects.create_user(username="supplier_global", email="b2b@globalpack.com", password="password123")
    UserProfile.objects.create(user=user_sup3, company=sup3, role_title="Logistics Operations Lead")

    # 3. Create Scoring Config for SME
    ScoringConfiguration.objects.create(
        sme_company=sme,
        w1_timeliness=0.40,
        w2_completeness=0.35,
        w3_price_consistency=0.25
    )

    # 4. Categories
    cat_elec = Category.objects.create(name="Electronic Components", description="Microchips, sensors, relays and circuitry")
    cat_mech = Category.objects.create(name="Mechanical & Hardware", description="Bearings, fasteners, brackets and motor parts")
    cat_raw = Category.objects.create(name="Raw Materials & Metals", description="Aluminum alloys, steel rods, polymers")
    cat_pack = Category.objects.create(name="Packaging & Logistics Supplies", description="Corrugated boxes, protective wrap, pallets")

    # 5. Products & Inventory Catalogue (36 Diversified Products)
    catalog = [
        # --- Atlas Industrial Components A.S. (Mechanical & Hardware) ---
        (sup1, cat_mech, "Industrial High-Load Deep Groove Ball Bearing 6205-2RS", "BRG-6205-2RS", 18.75, "Pieces", 140, 25, "Rack M-01 (Warehouse Alpha)"),
        (sup1, cat_mech, "High-Precision Linear Guideway Rail 20mm x 1000mm", "LGR-20-1000", 115.00, "Pieces", 45, 10, "Rack M-02 (Warehouse Alpha)"),
        (sup1, cat_mech, "Precision Ground Ball Screw C5 SFU1605-800mm", "BSC-1605-800", 85.50, "Pieces", 30, 8, "Rack M-03 (Warehouse Alpha)"),
        (sup1, cat_mech, "High-Torque Hybrid Stepper Motor NEMA 23 2.8Nm", "MOT-NEMA23-28", 48.00, "Pieces", 65, 15, "Rack M-04 (Warehouse Alpha)"),
        (sup1, cat_mech, "Heavy-Duty Pneumatic Compact Air Cylinder 50x100mm", "PNC-50-100", 62.00, "Pieces", 40, 12, "Rack M-05 (Warehouse Alpha)"),
        (sup1, cat_mech, "Flexible Jaw Coupling Shaft Coupler 8mm to 14mm", "CPL-JAW-0814", 12.50, "Pieces", 180, 30, "Rack M-06 (Warehouse Alpha)"),
        (sup1, cat_mech, "Industrial Flange Mounted Bearing Housing UCFL204", "BRG-UCFL-204", 22.00, "Pieces", 75, 20, "Rack M-07 (Warehouse Alpha)"),
        (sup1, cat_mech, "Stainless Steel Heavy-Duty Toggle Clamps 250kg", "CLP-TOG-250", 14.20, "Pieces", 110, 25, "Rack M-08 (Warehouse Alpha)"),
        (sup1, cat_mech, "Industrial Planetary Gearbox Reducer 10:1 Ratio", "GBX-PLN-1001", 165.00, "Pieces", 22, 6, "Rack M-09 (Warehouse Alpha)"),
        (sup1, cat_mech, "Hardened Steel T-Nut & Stud Fixture Clamping Set M12", "FIX-TNUT-M12", 54.00, "Sets", 50, 15, "Rack M-10 (Warehouse Alpha)"),
        (sup1, cat_mech, "Industrial Solenoid Air Valve 5/2 Way 24VDC", "VLV-SOL-52-24V", 38.50, "Pieces", 55, 12, "Rack M-11 (Warehouse Alpha)"),
        (sup1, cat_mech, "Cast Iron Pulley V-Belt Sheave 2-Groove Type B", "PLY-VBELT-2B", 29.00, "Pieces", 80, 18, "Rack M-12 (Warehouse Alpha)"),

        # --- TeknoSupply Electronics & Hardware (Electronics & Components) ---
        (sup2, cat_elec, "Microcontroller IC STM32-F407 32-bit ARM Cortex-M4", "IC-STM32-F407", 14.50, "Pieces", 320, 50, "Bay E-01 (Main Depot Izmir)"),
        (sup2, cat_elec, "Optocoupler Transistor Output 4-Channel SMD", "OPT-TR-4CH-SMD", 1.85, "Pieces", 850, 100, "Bay E-02 (Main Depot Izmir)"),
        (sup2, cat_elec, "Industrial Solid State Relay (SSR) 40A 240VAC", "SSR-40A-240V", 19.50, "Pieces", 90, 20, "Bay E-03 (Main Depot Izmir)"),
        (sup2, cat_elec, "DIN-Rail Industrial Power Supply 24VDC 10A 240W", "PSU-DIN-24V10A", 58.00, "Pieces", 70, 15, "Bay E-04 (Main Depot Izmir)"),
        (sup2, cat_elec, "Industrial Brushless DC Motor Driver 36V 15A CANBus", "DRV-BLDC-36V", 92.00, "Pieces", 35, 10, "Bay E-05 (Main Depot Izmir)"),
        (sup2, cat_elec, "High-Precision Temperature & Humidity Sensor Modbus RTU", "SNS-TH-MODBUS", 34.00, "Pieces", 60, 12, "Bay E-06 (Main Depot Izmir)"),
        (sup2, cat_elec, "PCB Screw Terminal Block 5.08mm 10-Pin Plug-in", "TMB-PCB-508-10P", 2.20, "Pieces", 600, 80, "Bay E-07 (Main Depot Izmir)"),
        (sup2, cat_elec, "Industrial RS485 to Ethernet Modbus Gateway", "GTW-RS485-ETH", 78.00, "Pieces", 28, 8, "Bay E-08 (Main Depot Izmir)"),
        (sup2, cat_elec, "Panel Mount Emergency Stop Button with 2NC Contacts", "BTN-ESTOP-2NC", 11.50, "Pieces", 140, 25, "Bay E-09 (Main Depot Izmir)"),
        (sup2, cat_elec, "Current Transducer Hall Effect 0-50A to 4-20mA", "SNS-CUR-50A-420", 42.00, "Pieces", 45, 10, "Bay E-10 (Main Depot Izmir)"),
        (sup2, cat_elec, "Precision Multiturn Wirewound Potentiometer 10k Ohm", "POT-10K-MULTI", 7.80, "Pieces", 210, 40, "Bay E-11 (Main Depot Izmir)"),
        (sup2, cat_elec, "High-Current Fast-Acting Ceramic Fuse 500V 32A", "FUS-CER-500V32A", 3.40, "Pieces", 450, 60, "Bay E-12 (Main Depot Izmir)"),

        # --- Global Pack & Polymer Materials Co. (Packaging & Raw Materials) ---
        (sup3, cat_pack, "Heavy-Duty Double Wall Corrugated Shipping Box 60x40x40cm", "BOX-DW-604040", 4.20, "Pieces", 650, 100, "Shed P-01 (Demirtas Facility)"),
        (sup3, cat_pack, "Anti-Static ESD Bubble Wrap Roll 100m x 1.2m", "BBL-ESD-100M", 38.00, "Rolls", 85, 20, "Shed P-02 (Demirtas Facility)"),
        (sup3, cat_pack, "Industrial Polyethylene Foam Corner Edge Protectors 100-Pack", "FPM-EDGE-100PK", 24.50, "Packs", 120, 30, "Shed P-03 (Demirtas Facility)"),
        (sup3, cat_pack, "Machine Grade Stretch Film 500mm x 23 Micron 16kg", "STR-MCH-23MIC", 52.00, "Rolls", 95, 25, "Shed P-04 (Demirtas Facility)"),
        (sup3, cat_pack, "Polypropylene Heavy-Duty Strapping Band 16mm x 2000m", "STP-PP-162000", 44.00, "Rolls", 60, 15, "Shed P-05 (Demirtas Facility)"),
        (sup3, cat_pack, "Direct Thermal Shipping Barcode Labels 100x150mm (500/Roll)", "LBL-TH-100150", 9.50, "Rolls", 340, 50, "Shed P-06 (Demirtas Facility)"),
        (sup3, cat_pack, "Euro-Standard Heavy Duty Wooden Pallet 1200x800mm (EPAL-1)", "PLT-EURO-EPAL1", 21.00, "Pieces", 180, 40, "Shed P-07 (Demirtas Facility)"),
        (sup3, cat_raw, "Aerospace Grade 6061-T6 Aluminum Solid Rod 25mm x 2m", "ALU-6061-T6-25", 36.50, "Rods", 110, 25, "Shed P-08 (Demirtas Facility)"),
        (sup3, cat_raw, "High-Density Polyethylene (HDPE) Virgin Injection Granules 25kg", "RAW-HDPE-25KG", 48.00, "Bags", 150, 35, "Shed P-09 (Demirtas Facility)"),
        (sup3, cat_raw, "Precision Ground Carbon Steel Shaft Rod 16mm x 1m (CK45)", "STL-CK45-161000", 26.00, "Rods", 95, 20, "Shed P-10 (Demirtas Facility)"),
        (sup3, cat_raw, "Extruded Polyoxymethylene (POM-C Acetal) Sheet 20mm x 500x1000mm", "POM-SHT-20MM", 88.00, "Sheets", 30, 8, "Shed P-11 (Demirtas Facility)"),
        (sup3, cat_raw, "Brass Round Bar Alloy CW614N 20mm x 1m", "BRS-CW614N-201M", 42.00, "Rods", 65, 15, "Shed P-12 (Demirtas Facility)")
    ]

    created_products = []
    for sup, cat, name, sku, price, unit, stock, threshold, loc in catalog:
        prod = Product.objects.create(
            name=name,
            sku=sku,
            category=cat,
            unit_price=price,
            unit=unit,
            preferred_supplier=sup
        )
        InventoryItem.objects.create(
            product=prod,
            company=sup,
            unit_price=price,
            current_stock=stock,
            critical_threshold=threshold,
            reorder_quantity=threshold * 4,
            warehouse_location=loc
        )
        created_products.append(prod)

    # 5.2 Multi-Vendor Competitive Offerings (Same Products Sold by Multiple Suppliers at Different Prices & Stock)
    competitor_offerings = [
        # (Supplier, Product SKU, Custom Unit Price, Stock, Threshold, Location)
        (sup1, "IC-STM32-F407", 16.20, 85, 20, "Rack E-01 (Umraniye Logistics Bay)"),
        (sup2, "BRG-6205-2RS", 21.00, 45, 10, "Bay M-02 (Izmir Distribution Center)"),
        (sup1, "BOX-DW-604040", 4.85, 120, 30, "Rack P-04 (Umraniye Facility)"),
        (sup1, "ALU-6061-T6-25", 39.00, 50, 15, "Rack R-01 (Umraniye Metals Shed)"),
        (sup1, "SSR-40A-240V", 22.50, 35, 10, "Bay E-03 (Umraniye Central)"),
        (sup2, "MOT-NEMA23-28", 52.50, 40, 12, "Bay M-05 (Izmir Electronics Hub)"),
        (sup1, "STR-MCH-23MIC", 56.00, 30, 10, "Rack P-02 (Umraniye Facility)"),
        (sup2, "LBL-TH-100150", 11.00, 80, 20, "Bay P-01 (Izmir Distribution Center)"),
        (sup1, "RAW-HDPE-25KG", 51.50, 40, 10, "Rack R-02 (Umraniye Facility)"),
        (sup1, "PSU-DIN-24V10A", 64.00, 25, 8, "Bay E-04 (Umraniye Central)"),
        (sup1, "STL-CK45-161000", 28.50, 60, 15, "Rack R-03 (Umraniye Facility)"),
        (sup1, "BTN-ESTOP-2NC", 13.00, 55, 15, "Bay E-09 (Umraniye Central)"),
        (sup2, "LGR-20-1000", 122.00, 20, 5, "Bay M-01 (Izmir Distribution Center)"),
        (sup3, "BRG-6205-2RS", 19.90, 70, 15, "Shed M-01 (Demirtas Facility)"),
        (sup2, "BBL-ESD-100M", 42.00, 50, 15, "Bay P-02 (Izmir Distribution Center)"),
        (sup1, "PLT-EURO-EPAL1", 23.50, 60, 15, "Rack P-01 (Umraniye Facility)")
    ]

    for sup, sku, comp_price, stock, threshold, loc in competitor_offerings:
        prod = Product.objects.filter(sku=sku).first()
        if prod:
            InventoryItem.objects.create(
                product=prod,
                company=sup,
                unit_price=comp_price,
                current_stock=stock,
                critical_threshold=threshold,
                reorder_quantity=threshold * 4,
                warehouse_location=loc
            )

    # 6. Create Realistic Purchase Orders with Evaluation Histories
    p1 = created_products[0]
    p2 = created_products[12]
    p3 = created_products[24]

    # Order 1: Delivered & Evaluated (High Score - Tier 1)
    po1 = PurchaseOrder.objects.create(
        order_number="PO-2026-0089",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup1,
        status="DELIVERED",
        expected_delivery_date=timezone.now().date() - timedelta(days=12),
        actual_delivery_date=timezone.now().date() - timedelta(days=12),
        is_evaluated=True,
        timeliness_score=98.0,
        completeness_score=100.0,
        price_consistency_score=95.0,
        evaluation_feedback="Excellent delivery! Components arrived on time with zero defects and full spec compliance.",
        evaluated_at=timezone.now() - timedelta(days=11),
        notes="Urgent delivery for Bursa Assembly Plant 1."
    )
    OrderItem.objects.create(order=po1, product=p1, quantity_requested=20, quantity_received=20, agreed_unit_price=18.75)
    po1.calculate_total()

    inv1 = Invoice.objects.create(
        invoice_number="INV-2026-0009",
        order=po1,
        issue_date=po1.actual_delivery_date,
        due_date=po1.actual_delivery_date + timedelta(days=30),
        tax_rate=20.0,
        payment_status="PAID"
    )
    inv1.update_totals()

    # Order 2: Delivered & Evaluated (Standard Score - Tier 2)
    po2 = PurchaseOrder.objects.create(
        order_number="PO-2026-0094",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup2,
        status="DELIVERED",
        expected_delivery_date=timezone.now().date() - timedelta(days=8),
        actual_delivery_date=timezone.now().date() - timedelta(days=7),
        is_evaluated=True,
        timeliness_score=85.0,
        completeness_score=92.0,
        price_consistency_score=90.0,
        evaluation_feedback="Slight 1-day delay during customs transit, but products functioned within tolerances.",
        evaluated_at=timezone.now() - timedelta(days=6),
        notes="Microcontrollers required for batch production run."
    )
    OrderItem.objects.create(order=po2, product=p2, quantity_requested=50, quantity_received=50, agreed_unit_price=14.50)
    po2.calculate_total()

    inv2 = Invoice.objects.create(
        invoice_number="INV-2026-0013",
        order=po2,
        issue_date=po2.actual_delivery_date,
        due_date=po2.actual_delivery_date + timedelta(days=30),
        tax_rate=20.0,
        payment_status="UNPAID"
    )
    inv2.update_totals()

    # Order 3: In Transit (En Route)
    po3 = PurchaseOrder.objects.create(
        order_number="PO-2026-0102",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup3,
        status="IN_TRANSIT",
        expected_delivery_date=timezone.now().date() + timedelta(days=2),
        notes="Cargo dispatched via Yurtiçi Lojistik tracking #YT-8839201."
    )
    OrderItem.objects.create(order=po3, product=p3, quantity_requested=100, quantity_received=0, agreed_unit_price=4.20)
    po3.calculate_total()

    # Order 4: Pending Supplier Confirmation (+1 Alert)
    po4 = PurchaseOrder.objects.create(
        order_number="PO-2026-0118",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup1,
        status="PENDING_SUPPLIER",
        expected_delivery_date=timezone.now().date() + timedelta(days=4),
        notes="Deliver to Receiving Gate 2."
    )
    OrderItem.objects.create(order=po4, product=created_products[1], quantity_requested=10, quantity_received=0, agreed_unit_price=115.00)
    po4.calculate_total()

    # 7. Compute Initial Supplier Evaluations
    refresh_all_supplier_evaluations()

    print("[SUCCESS] Database seeding completed successfully!")
    print(f"  - 1 SME Buyer: {sme.name}")
    print(f"  - 3 Verified Suppliers: {sup1.name}, {sup2.name}, {sup3.name}")
    print(f"  - 4 Categories & {len(catalog)} Rich Industrial Materials")
    print(f"  - 4 Sample Orders across lifecycle states with evaluations & invoices")

if __name__ == '__main__':
    run_seed()
