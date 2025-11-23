import os
import django
from redis import Redis

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from celery_app import app  # your configured Celery app

print("\n🔍 Checking Redis & Celery configuration...\n")

# Print relevant env vars and settings
redis_url = os.environ.get("REDIS_URL", "❌ NOT SET")
celery_broker = getattr(settings, "CELERY_BROKER_URL", "❌ NOT SET")

print(f"🌐 Environment REDIS_URL:         {redis_url}")
print(f"⚙️  Django CELERY_BROKER_URL:     {celery_broker}")

# Test Redis connection
try:
    r = Redis.from_url(celery_broker)
    pong = r.ping()
    if pong:
        print("✅ Redis connection successful (PING)")
    else:
        print("❌ Redis PING failed")
except Exception as e:
    print(f"❌ Redis connection error: {e}")

# Check transport and task registration from your actual app
try:
    transport = app.conf.broker_transport or "unknown"
    print(f"🚚 Celery broker transport (custom app): {transport}")
except Exception as e:
    print(f"❌ Celery transport check failed: {e}")

# List registered tasks
print("📋 Registered Celery tasks (custom app):")
for task_name in sorted(app.tasks.keys()):
    print(f"  • {task_name}")

# Run a test task
try:
    result = app.send_task("celery_app.debug_task")
    print(f"📤 Test task sent: ID={result.id}")
except Exception as e:
    print(f"❌ Could not send test task: {e}")
