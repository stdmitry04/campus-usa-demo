# server/core/management/commands/health_check.py
"""
django management command for health checking services
usage: python manage.py health_check
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import time
import json
import traceback
from datetime import datetime

import redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from celery import Celery


class Command(BaseCommand):
    help = 'check health of redis, qdrant, and celery services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='show detailed output including errors',
        )
        parser.add_argument(
            '--save-report',
            action='store_true',
            help='save detailed json report to file',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        save_report = options['save_report']

        checker = ServiceHealthChecker(verbose=verbose)
        healthy = checker.run_all_checks()

        if save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"health_check_report_{timestamp}.json"

            with open(report_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'summary': 'healthy' if healthy else 'unhealthy',
                    'results': checker.results
                }, f, indent=2)

            self.stdout.write(f"detailed report saved to: {report_file}")

        if healthy:
            self.stdout.write(
                self.style.SUCCESS('✅ all services are healthy!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ some services have issues')
            )


class ServiceHealthChecker:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {}

        # get urls from django settings or environment
        self.redis_url = getattr(settings, 'REDIS_URL',
                                 getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')

        print(f"checking services...")
        print(f"  redis: {self.redis_url}")
        print(f"  qdrant: {self.qdrant_url}")
        print("-" * 40)

    def check_redis(self):
        """test redis connection and operations"""
        print("🔴 testing redis...")
        try:
            client = redis.from_url(self.redis_url)

            # connectivity test
            ping_result = client.ping()
            if not ping_result:
                raise Exception("ping failed")

            # read/write test
            test_key = f"health_check_{int(time.time())}"
            test_value = "test_data_123"

            client.set(test_key, test_value, ex=60)
            retrieved_value = client.get(test_key).decode('utf-8')

            if retrieved_value != test_value:
                raise Exception("data mismatch")

            client.delete(test_key)

            # get redis info
            info = client.info()
            memory_used = info.get('used_memory_human', 'unknown')

            self.results['redis'] = {
                'status': 'healthy',
                'memory_used': memory_used,
                'connected_clients': info.get('connected_clients', 'unknown'),
                'redis_version': info.get('redis_version', 'unknown')
            }

            print(f"  ✅ redis working - memory: {memory_used}")

        except Exception as e:
            self.results['redis'] = {'status': 'unhealthy', 'error': str(e)}
            print(f"  ❌ redis failed: {e}")
            if self.verbose:
                print(f"     {traceback.format_exc()}")

    def check_qdrant(self):
        """test qdrant vector operations"""
        print("🟡 testing qdrant...")
        try:
            client = QdrantClient(url=self.qdrant_url)

            # basic connectivity
            health = client.get_cluster_info()

            # test collection operations
            test_collection = f"health_test_{int(time.time())}"

            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=4, distance=Distance.DOT)
            )

            # test vector crud
            test_points = [
                PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"test": "data1"})
            ]

            client.upsert(collection_name=test_collection, points=test_points)
            time.sleep(1)  # wait for indexing

            # test search
            search_result = client.search(
                collection_name=test_collection,
                query_vector=[0.1, 0.2, 0.3, 0.4],
                limit=1
            )

            if not search_result:
                raise Exception("search failed")

            # cleanup
            client.delete_collection(test_collection)

            # check storage type
            collections_count = len(client.get_collections().collections)
            storage_type = self._detect_storage_type()

            self.results['qdrant'] = {
                'status': 'healthy',
                'collections_count': collections_count,
                'storage_type': storage_type
            }

            print(f"  ✅ qdrant working - storage: {storage_type}")

        except Exception as e:
            self.results['qdrant'] = {'status': 'unhealthy', 'error': str(e)}
            print(f"  ❌ qdrant failed: {e}")
            if self.verbose:
                print(f"     {traceback.format_exc()}")

    def check_celery(self):
        """test celery worker connectivity"""
        print("🟢 testing celery...")
        try:
            # use django's celery app if available
            try:
                from celery_app import app
            except ImportError:
                # fallback to basic celery setup
                app = Celery('health_check')
                app.config_from_object({
                    'broker_url': self.redis_url,
                    'result_backend': self.redis_url,
                })

            # check for active workers
            inspect = app.control.inspect()
            active_workers = inspect.active()

            if not active_workers:
                raise Exception("no active workers found")

            # simple task test using inspect instead of actual task execution
            # this avoids issues with task registration in management commands
            stats = inspect.stats()
            worker_names = list(active_workers.keys())

            self.results['celery'] = {
                'status': 'healthy',
                'active_workers': len(worker_names),
                'worker_names': worker_names
            }

            print(f"  ✅ celery working - workers: {len(worker_names)}")

        except Exception as e:
            self.results['celery'] = {'status': 'unhealthy', 'error': str(e)}
            print(f"  ❌ celery failed: {e}")
            if self.verbose:
                print(f"     {traceback.format_exc()}")

    def _detect_storage_type(self):
        """detect storage configuration"""
        if os.getenv('DOCKER'):
            if os.path.exists('/qdrant/storage'):
                return 'docker persistent volume'
            else:
                return 'docker memory storage'
        elif 'amazonaws.com' in self.qdrant_url or os.getenv('AWS_REGION'):
            if os.path.exists('/qdrant/storage'):
                return 'aws efs persistent'
            else:
                return 'aws memory only'
        else:
            return 'local development'

    def run_all_checks(self):
        """run all health checks"""
        self.check_redis()
        self.check_qdrant()
        self.check_celery()

        # summary
        print("\n" + "="*40)
        print("HEALTH CHECK SUMMARY")
        print("="*40)

        all_healthy = True
        for service, result in self.results.items():
            status = result.get('status', 'unknown')
            if status == 'healthy':
                print(f"✅ {service.upper()}: {status}")
            else:
                print(f"❌ {service.upper()}: {status}")
                all_healthy = False

        storage_type = self._detect_storage_type()
        print(f"💾 STORAGE: {storage_type}")

        return all_healthy