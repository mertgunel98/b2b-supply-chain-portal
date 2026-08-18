# 📦 B2B Supply Chain, Inventory & Supplier Performance Portal (MIS 498)

A comprehensive B2B Supply Chain & Marketplace Management platform built with **Django REST Framework**, **Vanilla CSS / Modern JavaScript**, and **ReportLab PDF Generator**.

---

## 🚀 Core Features

### 1. 🛒 B2B Materials Marketplace
- Multi-supplier catalog with 35+ industrial, mechanical, electronic, and raw material products.
- Instant 1-Click Purchase Order issuance with customizable quantities and delivery terms.
- Real-time search and multi-criteria category/vendor filtering.

### 2. 📦 Isolated Supplier Inventory & Dynamic Safety Thresholds
- Each supplier manages only their own catalog materials and stock levels.
- **Safety Threshold (Emniyet Stoku):** Live-editable critical buffer per material.
- **🚨 Automated Shortage Alerts:** Triggers red status badges and real-time dashboard notifications when stock drops below safety margins.
- In-place unit price updates and restock batch actions.

### 3. 📑 Order Lifecycle Management & Rejection Workflows
- **Buyer Capabilities:** Issue orders, track shipments, generate official PO PDFs, receive cargo, rate delivered orders, and cancel/reject orders.
- **Supplier Capabilities:** Real-time incoming order notifications with glowing **`+1`** badge, accept & confirm orders, ship cargo, generate tax invoice PDFs, or decline incoming orders.

### 4. ⭐ Mathematical Multi-Criteria Supplier Evaluation Model
Delivered purchase orders are dynamically evaluated by buyers across three core weighted criteria:

$$\text{Performance Score} = (0.40 \times \text{Timeliness } W_1) + (0.35 \times \text{Completeness } W_2) + (0.25 \times \text{Price Consistency } W_3)$$

- **$W_1$ (40%) Delivery Timeliness:** Fulfillment speed relative to agreed due dates.
- **$W_2$ (35%) Order Completeness:** Ratio of delivered vs. ordered units without defect.
- **$W_3$ (25%) Price Consistency:** Price stability and catalog adherence.
- Automated Tier Classification: **Tier 1 (Preferred / 90%+), Tier 2 (Standard / 75-89%), Tier 3 (Under Review / <75%)**.

### 5. 📄 Enterprise PDF Documentation Engine
- High-fidelity **Purchase Order** and **Commercial Tax Invoice** PDFs generated on-the-fly with ReportLab.
- Comprehensive corporate identity resolution (Tax IDs, OSB plant addresses, authorized signatories, VAT breakdowns).

---

## 🛠️ Technology Stack
- **Backend:** Python 3.13, Django 5.x, Django REST Framework
- **Frontend:** HTML5, CSS3 (Custom Design System, Glassmorphism, Responsive), Vanilla JS
- **PDF Engine:** ReportLab
- **Database:** SQLite / PostgreSQL ready

---

## ⚙️ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/mertgunel98/b2b-supply-chain-portal.git
cd b2b-supply-chain-portal

# 2. Install dependencies
pip install django djangorestframework reportlab django-cors-headers

# 3. Apply database migrations
python manage.py migrate

# 4. Start development server
python manage.py runserver 127.0.0.1:8000
```

Access the portal at `http://127.0.0.1:8000`.

---

## 👤 Author
- **MERT Günel** - MIS 498 Project
