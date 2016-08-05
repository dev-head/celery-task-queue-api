#
# ************************************************************************
# This configuration file is handled by puppet, please update the proper template
# ************************************************************************
#
#
# config file for Celery Tasks
from kombu import Exchange, Queue

# Define the queue broker, the service responsible
# for holding messages that the tasks will consume.
BROKER_URL = 'amqp://celeryman:more2be@dev.local:5672/queue'

BROKER_TRANSPORT_OPTIONS = {'ack_emulation': False} 
BROKER_CONNECTION_MAX_RETRIES = 0 # forever
BROKER_HEARTBEAT = 10
BROKER_POOL_LIMIT = 1000
CELERY_IGNORE_RESULT = False
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True
CELERY_MESSAGE_COMPRESSION = 'gzip'
CELERY_DEFAULT_RATE_LIMIT = '1000/s'
CELERY_ACKS_LATE = False
CELERYD_PREFETCH_MULTIPLIER = 10

# Define result storage engine
# we are using redis for simple key => val store
CELERY_RESULT_BACKEND = 'redis://dev.local:6379/'

# Define the task result timeout period
# Keeping this low will reduce overhead on redis and the server.
CELERY_TASK_RESULT_EXPIRES=20

CELERY_TIMEZONE="America/Los_Angeles"

# Json is language agnostic, these settings enforce 
# what message data is allowed to be passed around
# and sets the expectations for that data.
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Here we define our default queue to watch
# If we decide to set up unique queues based for each task
# we can override these in the configuration on the task
#
# Transient queue can be used for messages that can be lost.
# This doesn't save anything to disk resulting in a faster queue level 
# but more volitile, so be sure that message can be lost if using queue.
CELERY_CREATE_MISSING_QUEUES   = 'true'
CELERY_DEFAULT_QUEUE = 'queue'
CELERY_QUEUES = (
    Queue('queue', Exchange('queue'), routing_key='queue'),
    Queue('queue_transient', Exchange('queue_transient'), routing_key='queue_transient', delivery_mode=1),
    Queue('queue_feed', Exchange('queue_feed'), routing_key='queue_feed'),
    Queue('queue_image', Exchange('queue_image'), routing_key='queue_image'),
    Queue('queue_data', Exchange('queue_data'), routing_key='queue_data', delivery_mode=1),
)

# Main task configuration done here vs the task file for easier readability
# any of these can be set in the task @def 
CELERY_ANNOTATIONS = {
    'tqueue.route_task': {'rate_limit': '20000/s','track_started': 'true'},
    'tqueue.route_task_transient': {'rate_limit': '20000/s', 'ignore_result':'true' },
    'tqueue.route_feed': {'rate_limit': '20000/s'},
    'tqueue.route_image': {'rate_limit': '20000/s', 'ignore_result':'false'},
    'tqueue.route_data': {'rate_limit': '20000/s', 'ignore_result':'false' },
}

# More of an example of mapping a single task to it's own queue.
# This is useful if we end up splitting out tasks a bit more and need
# to control the queue configurations such as rate limiting, etc.
CELERY_ROUTES = {
    'queue.tasks.route_email': {'queue': 'queue_transient'},
    'queue.tasks.route_task': {'queue': 'queue'},
    'queue.tasks.route_task_transient': {'queue': 'queue_transient'},
    'queue.tasks.route_feed': {'queue': 'queue_feed'},
    'queue.tasks.route_image': {'queue': 'queue_image'},
    'queue.tasks.route_data': {'queue': 'queue_data'}
}
