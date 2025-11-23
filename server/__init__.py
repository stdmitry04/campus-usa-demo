# this ensures celery auto-discovery works properly in django
try:
    from celery_app import app as celery_app
    __all__ = ('celery_app',)
    print(app.conf.broker_url)
    print(app.conf.result_backend)
except ImportError:
    # fallback for different import paths
    try:
        from .celery_app import app as celery_app
        __all__ = ('celery_app',)
        print(celery_app.conf.broker_url)
        print(celery_app.conf.result_backend)
    except ImportError:
        pass