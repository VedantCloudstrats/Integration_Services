import os
import sys
import django

# Add project root to python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize Django ORM context for tests
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SWMM.settings")
django.setup()
