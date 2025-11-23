# import os
# import sys
# import django
# from celery import Celery
#
# # ------------------------------------------------------------------ #
# # 0) Ensure project root is in sys.path so "server.x" imports work   #
# # ------------------------------------------------------------------ #
# # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to /campus-usa
# # if BASE_DIR not in sys.path:
# #     sys.path.insert(0, BASE_DIR)
#
# # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# # ------------------------------------------------------------------ #
#
# # Ensure 'server/' is in sys.path so 'core' can be found
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# if BASE_DIR not in sys.path:
#     sys.path.insert(0, BASE_DIR)
#
#
# # 1) Set DJANGO_SETTINGS_MODULE and initialize Django                #
# # ------------------------------------------------------------------ #
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()
#
# # ------------------------------------------------------------------ #
# # 2) Set up Celery                                                   #
# # ------------------------------------------------------------------ #
# app = Celery("campus_usa")
# app.config_from_object("django.conf:settings", namespace="CELERY")
#
# # 3) Discover tasks
# app.autodiscover_tasks([
#     "server.core.tasks",
#     "server.documents.tasks",
# ])
#
# # 4) Force-load if needed
# import server.core.tasks.ocr_tasks         # noqa: F401
# import server.core.tasks.embedding_tasks   # noqa: F401
#
# @app.task(bind=True)
# def debug_task(self):
#     print(f"Request: {self.request!r}")

"""
celery_app.py – updated for flat docker layout
"""

import os
import sys
import django
from celery import Celery
from celery import _state

# ensure the current directory is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# set django settings and initialize
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


from django.conf import settings
print("📦 CELERY_BROKER_URL:", getattr(settings, "CELERY_BROKER_URL", None))





# proper django setup for celery
try:
    django.setup()
    print("✅ django setup successful for celery")
except Exception as e:
    print(f"❌ django setup failed: {e}")
    # try to configure django manually if auto-setup fails
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()

# create celery app
app = Celery("college_app_demo")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Fallback to Redis only if not already configured
if not app.conf.broker_url or app.conf.broker_url.startswith("memory://"):
    app.conf.broker_url = "redis://localhost:6379/0"
    app.conf.result_backend = "redis://localhost:6379/0"
    app.conf.broker_transport = "redis"
    print("⚠️ Forced Redis config")
else:
    print("✅ Using Django Celery settings")

# Register as default Celery app (after it’s configured)
_state.default_app = app


# discover tasks from django apps
app.autodiscover_tasks([
    "core.tasks",
])

# manually import task modules to ensure they're loaded
# wrap in try-except to handle import errors gracefully
try:
    import core.tasks.ocr_tasks           # noqa: F401
    import core.tasks.embedding_tasks     # noqa: F401
    import core.tasks.validation_tasks
    print("✅ celery tasks loaded successfully")
except ImportError as e:
    print(f"⚠️ warning: could not import some tasks: {e}")

@app.task(bind=True)
def debug_task(self):
    """debug task to test celery functionality"""
    print(f"Request: {self.request!r}")
    return "celery is working!"