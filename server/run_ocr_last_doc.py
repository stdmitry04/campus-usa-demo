import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from core.tasks.ocr_tasks import process_document_ocr_task

# Get the Document model dynamically
Document = apps.get_model('documents', 'Document')

# Get the last document
last_doc = Document.objects.order_by("-created_at").first()

if not last_doc:
    print("❌ No documents found.")
    exit()

print(f"✅ Found last document: {last_doc.id} (user {last_doc.user_id})")

# 🧠 DEBUG: Check which Celery app is bound to the task
print(f"[DEBUG] OCR task is bound to Celery app: {process_document_ocr_task.app!r}")
if process_document_ocr_task.app.main == '__main__':
    print("❌ Task is using default Celery app (__main__) — likely misconfigured.")
else:
    print(f"✅ Task is bound to named app: {process_document_ocr_task.app.main}")

# 📨 Send OCR task
try:
    from django.conf import settings
    print(f"[DEBUG] CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")

    result = process_document_ocr_task.delay(user_id=last_doc.user_id, document_id=str(last_doc.id))
    print(f"📤 OCR task scheduled with ID: {result.id}")
except Exception as e:
    print(f"❌ Failed to schedule task: {e}")
