import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_core.settings')
application = get_wsgi_application()

# Auto-seed database on server boot if empty or partial (for Render persistence)
try:
    from apps.inventory.models import InventoryItem
    if InventoryItem.objects.count() < 30:
        print("[AUTO-SEED] Auto-seeding full B2B multi-vendor catalog...")
        from seed_data import run_seed
        run_seed()
except Exception as e:
    print("[AUTO-SEED WARNING]", e)
