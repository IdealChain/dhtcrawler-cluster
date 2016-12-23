from datetime import timedelta
from kombu import Exchange, Queue

torrents_dir = './../torrents'

broker_url = 'redis://'
task_time_limit = 30.0
worker_task_log_format = """[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s: %(message)s"""

result_backend = 'redis://'
result_expires = timedelta(minutes=5)
result_persistent = True

beat_schedule = {
    'backend-cleanup': {
        'task': 'celery.backend_cleanup',
        'schedule': timedelta(minutes=5),
    },
    'print-stats': {
        'task': 'tasks.print_stats',
        'schedule': timedelta(minutes=1),
    }
}

task_queues = (
    Queue('celery', Exchange('celery'), routing_key='celery', durable=False),
)
