from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import Company
from apps.inventory.models import Category, Product, InventoryItem
from apps.orders.models import PurchaseOrder, OrderItem, Invoice
from apps.orders.pdf_generator import generate_order_pdf, generate_invoice_pdf
from apps.scoring.algorithm import calculate_supplier_score
from apps.scoring.models import ScoringConfiguration

class B2BSupplyChainTests(TestCase):
    def setUp(self):
        # 1. Create Companies
        self.sme = Company.objects.create(
            name="Apex Manufacturing Ltd.",
            company_type="SME",
            email="procurement@apex.com"
        )
        self.supplier = Company.objects.create(
            name="TeknoSupply Co.",
            company_type="SUPPLIER",
            email="sales@teknosupply.com"
        )
        
        # 2. Create Category & Product
        self.category = Category.objects.create(name="Electronic Components")
        self.product = Product.objects.create(
            name="Microcontroller IC STM32",
            sku="IC-STM32-01",
            category=self.category,
            unit="Pieces",
            unit_price=12.50,
            preferred_supplier=self.supplier
        )

        # 3. Create Inventory Item with Critical Alert
        self.inv_item = InventoryItem.objects.create(
            company=self.sme,
            product=self.product,
            current_stock=10,
            critical_threshold=25,
            reorder_quantity=100
        )

    def test_critical_stock_alert(self):
        """Validates that stock at 10 with threshold 25 triggers critical alert."""
        self.assertTrue(self.inv_item.is_critical)
        self.assertEqual(self.inv_item.stock_health_status, 'CRITICAL')

    def test_supplier_scoring_algorithm(self):
        """Validates weighted multi-criteria supplier scoring calculation."""
        # Create an on-time order
        po = PurchaseOrder.objects.create(
            order_number="PO-TEST-001",
            buyer_company=self.sme,
            supplier_company=self.supplier,
            status="DELIVERED",
            expected_delivery_date=timezone.now().date(),
            actual_delivery_date=timezone.now().date()
        )
        OrderItem.objects.create(
            order=po,
            product=self.product,
            quantity_requested=50,
            quantity_received=50,
            agreed_unit_price=12.50
        )

        # Compute score with weights W1=0.5, W2=0.3, W3=0.2
        custom_weights = {'w1': 0.5, 'w2': 0.3, 'w3': 0.2}
        score = calculate_supplier_score(self.sme, self.supplier, custom_weights)
        
        self.assertGreaterEqual(score['overall_score'], 90.0)
        self.assertEqual(score['on_time_count'], 1)
        self.assertEqual(score['delayed_count'], 0)

    def test_pdf_generation(self):
        """Ensures PDF generator creates binary PDF stream without errors."""
        po = PurchaseOrder.objects.create(
            order_number="PO-PDF-TEST",
            buyer_company=self.sme,
            supplier_company=self.supplier,
            status="CONFIRMED",
            expected_delivery_date=timezone.now().date() + timedelta(days=7)
        )
        OrderItem.objects.create(
            order=po,
            product=self.product,
            quantity_requested=20,
            agreed_unit_price=12.50
        )
        po.calculate_total()
        
        pdf_bytes = generate_order_pdf(po)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
