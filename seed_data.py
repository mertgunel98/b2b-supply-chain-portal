"""
Database Seeder for B2B Supply Chain and Inventory Tracking Portal.
Populates realistic SMEs, Suppliers, Products, Stock entries (healthy & critical), Purchase Orders, and Invoices.
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
    print("[INFO] Starting B2B Portal database seeding...")

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
        contact_person="Mert Guner (Head of Supply Chain)"
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

    # 5. Products
    p1 = Product.objects.create(
        name="Microcontroller IC STM32-F407",
        sku="IC-STM32-F407",
        category=cat_elec,
        unit="Pieces",
        unit_price=14.50,
        preferred_supplier=sup2,
        description="High-performance ARM Cortex-M4 MCU, 168 MHz with 1MB Flash."
    )

    p2 = Product.objects.create(
        name="Industrial Aluminum Profile 40x40 (3m)",
        sku="ALU-PROF-4040",
        category=cat_raw,
        unit="Meters",
        unit_price=28.00,
        preferred_supplier=sup1,
        description="T-Slot modular anodized aluminum extrusion for CNC frames."
    )

    p3 = Product.objects.create(
        name="Precision Ball Bearing 608-2RS",
        sku="BRG-608-2RS",
        category=cat_mech,
        unit="Sets (10 pcs)",
        unit_price=18.75,
        preferred_supplier=sup1,
        description="Double rubber sealed deep groove chrome steel bearings."
    )

    p4 = Product.objects.create(
        name="Heavy-Duty Corrugated Shipping Boxes (50x40x30)",
        sku="BOX-504030-HD",
        category=cat_pack,
        unit="Bundles (25 pcs)",
        unit_price=42.50,
        preferred_supplier=sup3,
        description="Double wall corrugated export cardboard boxes with high crush resistance."
    )

    p5 = Product.objects.create(
        name="Solid State Relay 40A SSR-40DA",
        sku="RELAY-SSR-40DA",
        category=cat_elec,
        unit="Pieces",
        unit_price=11.20,
        preferred_supplier=sup2,
        description="Opto-isolated DC to AC solid state relay with LED indicator."
    )

    p6 = Product.objects.create(
        name="High-Tensile Steel Hex Bolts M8x50 (Grade 8.8)",
        sku="BOLT-M8-50-G88",
        category=cat_mech,
        unit="Boxes (100 pcs)",
        unit_price=22.00,
        preferred_supplier=sup1,
        description="Zinc plated metric Grade 8.8 steel fastening bolts."
    )

    # 6. Inventory Items (Include CRITICAL stock items to showcase alert badge!)
    InventoryItem.objects.create(
        company=sme,
        product=p1,
        current_stock=12,           # CRITICAL (Threshold is 30)
        critical_threshold=30,
        reorder_quantity=150,
        warehouse_location="Warehouse A - Shelf E-04"
    )

    InventoryItem.objects.create(
        company=sme,
        product=p2,
        current_stock=85,           # HEALTHY
        critical_threshold=25,
        reorder_quantity=80,
        warehouse_location="Warehouse B - Heavy Rack R-1"
    )

    InventoryItem.objects.create(
        company=sme,
        product=p3,
        current_stock=18,           # CRITICAL (Threshold is 20)
        critical_threshold=20,
        reorder_quantity=100,
        warehouse_location="Warehouse A - Bin B-12"
    )

    InventoryItem.objects.create(
        company=sme,
        product=p4,
        current_stock=8,            # CRITICAL (Threshold is 15)
        critical_threshold=15,
        reorder_quantity=50,
        warehouse_location="Logistics Hub - Pallet Bay 03"
    )

    InventoryItem.objects.create(
        company=sme,
        product=p5,
        current_stock=64,           # HEALTHY
        critical_threshold=20,
        reorder_quantity=60,
        warehouse_location="Warehouse A - Shelf E-09"
    )

    InventoryItem.objects.create(
        company=sme,
        product=p6,
        current_stock=110,          # HEALTHY
        critical_threshold=40,
        reorder_quantity=120,
        warehouse_location="Warehouse B - Bin M-02"
    )

    # 7. Purchase Orders & Invoices (Historical & Active)
    today = timezone.now().date()

    # Order 1 (Delivered on time, Invoiced & Paid)
    po1 = PurchaseOrder.objects.create(
        order_number="PO-2026-0089",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup1,
        status="DELIVERED",
        expected_delivery_date=today - timedelta(days=12),
        actual_delivery_date=today - timedelta(days=13), # Delivered 1 day early!
        notes="Standard monthly replenishment for CNC modular frame project."
    )
    item1_1 = OrderItem.objects.create(order=po1, product=p2, quantity_requested=60, quantity_received=60, agreed_unit_price=28.00)
    item1_2 = OrderItem.objects.create(order=po1, product=p3, quantity_requested=80, quantity_received=80, agreed_unit_price=18.75)
    po1.calculate_total()

    inv1 = Invoice.objects.create(
        invoice_number="INV-2026-7701",
        order=po1,
        issue_date=today - timedelta(days=12),
        due_date=today + timedelta(days=18),
        tax_rate=20.00,
        payment_status="PAID"
    )
    inv1.update_totals()

    # Order 2 (Delivered with 1 day delay from TeknoSupply)
    po2 = PurchaseOrder.objects.create(
        order_number="PO-2026-0094",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup2,
        status="DELIVERED",
        expected_delivery_date=today - timedelta(days=6),
        actual_delivery_date=today - timedelta(days=5), # 1 day late
        notes="Urgent batch for IoT temperature telemetry sensors."
    )
    item2_1 = OrderItem.objects.create(order=po2, product=p1, quantity_requested=100, quantity_received=100, agreed_unit_price=14.50)
    item2_2 = OrderItem.objects.create(order=po2, product=p5, quantity_requested=40, quantity_received=40, agreed_unit_price=11.20)
    po2.calculate_total()

    inv2 = Invoice.objects.create(
        invoice_number="INV-2026-7744",
        order=po2,
        issue_date=today - timedelta(days=5),
        due_date=today + timedelta(days=25),
        tax_rate=20.00,
        payment_status="UNPAID"
    )
    inv2.update_totals()

    # Order 3 (In Transit from Global Pack)
    po3 = PurchaseOrder.objects.create(
        order_number="PO-2026-0102",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup3,
        status="IN_TRANSIT",
        expected_delivery_date=today + timedelta(days=2),
        notes="Custom export packaging boxes with fragile water-resistant labeling."
    )
    item3_1 = OrderItem.objects.create(order=po3, product=p4, quantity_requested=40, quantity_received=0, agreed_unit_price=42.50)
    po3.calculate_total()

    # Order 4 (Pending Supplier Confirmation)
    po4 = PurchaseOrder.objects.create(
        order_number="PO-2026-0118",
        order_type="PURCHASE_ORDER",
        buyer_company=sme,
        supplier_company=sup1,
        status="PENDING_SUPPLIER",
        expected_delivery_date=today + timedelta(days=7),
        notes="Fastening bolts restock."
    )
    item4_1 = OrderItem.objects.create(order=po4, product=p6, quantity_requested=80, quantity_received=0, agreed_unit_price=22.00)
    po4.calculate_total()

    # 8. Refresh and compute all supplier scores
    refresh_all_supplier_evaluations(sme)

    print("[SUCCESS] Database seeding completed successfully!")
    print(f"   - 1 SME Company: {sme.name}")
    print(f"   - 3 Suppliers: {sup1.name}, {sup2.name}, {sup3.name}")
    print(f"   - 4 Categories & 6 Products")
    print(f"   - 6 Inventory Items (3 in CRITICAL status triggering alerts)")
    print(f"   - 4 Purchase Orders across lifecycle stages with 2 Invoices")

if __name__ == '__main__':
    run_seed()
