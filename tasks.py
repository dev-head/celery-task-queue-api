from __future__ import absolute_import
from celery.utils.log import get_task_logger
from tqueue.celery import app

# Bring in the task logger for all to share.
logger = get_task_logger(__name__)

# Main class to encapsulate the error handling. 
class TaskError(Exception):
    def __init__(self, status_code, message=None, error=None, ):
        self.status_code = status_code
        self.message = message
        self.error = error
        super(TaskError, self).__init__(status_code, message, error)

# 
# TaskRouter class used to encapsulate the share routing 
# functionality of our tasks. Some tasks have their own 
# custom rate limits and functionality needs, this class
# is used to satisify the defaults in order to reduce code
#
# @param dict kwargs passed from the message that was passed to the task
##################################################
class TaskRouter:
  def __init__(self, **kwargs):
  
    # Define our imports up front.
    import json, subprocess
    
    # Hard coding paths for increase speed.
    hhvm         = 'hhvm'
    app_path   = '/srv/app/bin/cli'
    task_name = ''
    celery_task = ''
    wait_for_response = 'true'

    command_args  = []
    #command_args.append(hhvm)
    command_args.append(app_path)

    if 'wait_for_response' in kwargs:
      wait_for_resposne = kwargs['wait_for_response']

    if 'celery_task' in kwargs:
      celery_task=kwargs['celery_task']

     # Add in the task name that we will be calling.
    if 'task_name' in kwargs:
      task_name = kwargs['task_name']
      if task_name:
        command_args.append(kwargs['task_name'])

    # Convert arguments into string so we can add them
    # to the command. @note: these should be passed
    # in the order that they are needed on to be consumed by the command
    if 'task_args' in kwargs:
      convert_args_dirty=kwargs['task_args']
      if convert_args_dirty:
        
        # Task args may have been passed as json so we need to conver
        # them back to their native type, iteration and type checking does this.
        for key in convert_args_dirty: 
          if type (key) is list:
            command_args.append(json.dumps(key))
          else:
            command_args.append(key)

    # Convert task options into a string so we can add them 
    # to the command. @note: these are expected to be key / value
    # data sets, not deeper nested arrays.
    if 'task_options' in kwargs:
      
      task_options_dirty=kwargs['task_options']
      
      if task_options_dirty:
        for key,val in task_options_dirty.iteritems(): 
          if val == '':
            task_option  = '--' + key
          else:
            task_option  = '--' + key + '=' + val
          command_args.append(task_option)

    logger.info('')
    logger.info('++++++++++++++++++')
    logger.info('[CELERY]::[' + celery_task + ']::[BEGIN]')
    logger.info('task_name::[' + task_name + ']')
    logger.debug('command_args::')
    logger.debug(command_args)

    # Kick off pass through to shell keeping 
    # track of the output and error return from the script 
    # making it available to us later on.

    if wait_for_response:
      p = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
      (response, err) = p.communicate()
      logger.debug('[RESPONSE]::' + response)
      logger.debug('[ERROR]::' + err)

      if err or p.returncode:
        raise TaskError(500, "Task [%s::%s] Failed with exit code %i" % (celery_task, task_name, p.returncode), err)

    else:
      p = subprocess.Popen(command_args, stdout=None, stderr=None, close_fds=True, shell=False)

    logger.info('[CELERY]::[' + celery_task + ']::[END]')
    logger.info('====================')

#
# route_email task used to for testing purposes
##################################################
@app.task(name='tqueue.route_email')
def email(**kwargs):
  import smtplib
  from email.mime.text import MIMEText
  from subprocess import Popen, PIPE
  msg = MIMEText(kwargs['message'])

  logger.info('TESTING ROUTE_EMAIL')
  logger.info(kwargs['to'])
  logger.info(kwargs['message'])
  logger.info(kwargs['subject'])

  if kwargs['to'] and kwargs['message'] and kwargs['subject']:
    msg["From"] = kwargs['to']
    msg["To"] = kwargs['to']
    msg["Subject"] = kwargs['subject']
    p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
    result = p.communicate(msg.as_string())

  return result

# Base task used to route through to the main controller for the php application.
# This is used as a catch all and is wide open for use, when there's a need for more
# control on workers and rate limiting, you should create a new task and 
# call directly to that instead of this one. 
#
##################################################

@app.task(
  name='tqueue.route_taskxxx',
)
def self(self, *args, **kwargs):
  logger.info('sup bitches')
  
  return

@app.task(
  name='tqueue.route_taskxxx',
  throws=(TaskError),
  bind=True, 
  max_retries=1
)
def route_taskxxx(self, *args, **kwargs):
  kwargs['celery_task'] = 'route_task'
  kwargs['wait_for_response'] = 'true'
  
  try: 
    TaskRouter(**kwargs)
  except TaskError as e:
    logger.info('Caught Exception::retrying...')
    raise self.retry(exc=e, countdown=10)
    #raise TaskError(500, 'Task Failed', e)
  except Exception as e:
    logger.info('UN-Caught Exception::retrying...')
    logger.exception(e)

  return 
##################################################

#
# route_task_transient
##################################################
@app.task(
  name='tqueue.route_task_transient', 
  throws=(TaskError, 500)
)
def route_task_transient(**kwargs):
  kwargs['celery_task'] = 'route_task_transient'

  try: 
    TaskRouter(**kwargs)
  except TaskError as e:
    raise TaskError(500, 'Task Failed', e)
  except Exception as e:
    logger.exception(e)
    raise TaskError(501, 'Task Failed - Exception thrown in the TaskRouter', e)
  except:
    raise TaskError(502, 'Task Failed - Unknown Exception thrown in the TaskRouter', '')
  
  return 
##################################################

#
# route_feed used for watching the feed queue.
##################################################
@app.task(
  name='tqueue.route_feed', 
  throws=(TaskError, 500)
)
def route_feed(**kwargs):
  kwargs['celery_task'] = 'route_feed'

  try: 
    TaskRouter(**kwargs)
  except TaskError as e:
    raise TaskError(500, 'Task Failed', e)
  except Exception as e:
    logger.exception(e)
    raise TaskError(501, 'Task Failed - Exception thrown in the TaskRouter', e)
  except:
    raise TaskError(502, 'Task Failed - Unknown Exception thrown in the TaskRouter', '')
  
  return 
##################################################

#
# route_image used for watching the feed queue.
##################################################
@app.task(
  name='tqueue.route_image', 
  throws=(TaskError, 500)
)
def route_image(**kwargs):
  kwargs['celery_task'] = 'route_image'

  try: 
    TaskRouter(**kwargs)
  except TaskError as e:
    raise TaskError(500, 'Task Failed', e)
  except Exception as e:
    logger.exception(e)
    raise TaskError(501, 'Task Failed - Exception thrown in the TaskRouter', e)
  except:
    raise TaskError(502, 'Task Failed - Unknown Exception thrown in the TaskRouter', '')
  
  return 
##################################################

#
# route_data used for watching the feed queue.
##################################################
@app.task(
  name='tqueue.route_data', 
  throws=(TaskError, 500)
)
def route_data(**kwargs):
  kwargs['celery_task'] = 'route_data'

  try: 
    TaskRouter(**kwargs)
  except TaskError as e:
    raise TaskError(500, 'Task Failed', e)
  except Exception as e:
    logger.exception(e)
    raise TaskError(501, 'Task Failed - Exception thrown in the TaskRouter', e)
  except:
    raise TaskError(502, 'Task Failed - Unknown Exception thrown in the TaskRouter', '')
  
  return 
##################################################
