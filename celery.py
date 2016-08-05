from __future__ import absolute_import

from celery import Celery
from tqueue import celeryconfig

app = Celery('tqueue', 
    include = ['tqueue.tasks'], 
    serializer='json',
    )

app.config_from_object(celeryconfig)

if __name__ == '__main__':
    app.start()

