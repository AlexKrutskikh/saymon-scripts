#!/usr/bin/python
# -*- coding: utf-8 -*-


# %%

import datetime as DT
import sys
import logging
import logging.config
import time

DEFAULT_LOGGING = {
    'version': 1,
    'formatters': { 
        'standard': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)s %(funcName)s(%(lineno)d) %(message)s',         
            'datefmt': '%d.%m.%Y %H:%M:%S' },
    },
    'handlers': {
        'console':  {'class': 'logging.StreamHandler', 
                     'formatter': "standard", 
                     'level': 'CRITICAL', 
                     'stream': sys.stdout},
        'file':     {'class': 'logging.handlers.RotatingFileHandler', 
                     'formatter': "standard", 
                     'level': 'DEBUG', 
# указать путь до места хранения лог-файла работы платформы /var/logs
# sudo mkdir /var/log/saymon
# saymon@home:/var/log$ sudo mkdir /var/log/saymon/laim
# saymon@home:/var/log$ sudo chown saymon /var/log/saymon/laim
                     'filename': 'C:\\Users\kruts\OneDrive\Desktop\PythonProject\saymon-scripts\\Unit_Bulk_Operations/laim.log',
                     'mode': 'a',
                     'maxBytes': 5*1024*1024,
                     'backupCount': 2,
                     'encoding': 'utf-8',
                     'delay': 0} 
    },
    'loggers': { 
        __name__:   {'level': 'DEBUG', 
                     'handlers': ['console', 'file'], 
                     'propagate': False},
    }
}

logging.config.dictConfig(DEFAULT_LOGGING)
print_log = logging.getLogger(__name__)
print_log.info("____________________________________________________________________________________________________")
print_log.info(" - logging initiated")

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} took {end_time - start_time} seconds to run.")
        return result
    return wrapper
#Вы можете использовать этот декоратор для определения времени выполнения функции: @timing_decorator

def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Executing {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"Finished executing {func.__name__}")
        return result
    return wrapper

# так можно применить декоратор:
#   @log_execution
#   def extract_data(source):
#     # extract data from source
#     data = ...

# Пример декоратора нотификаций

# import smtplib
# import traceback
# from email.mime.text import MIMEText

# def email_on_failure(sender_email, password, recipient_email):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             try:
#                 return func(*args, **kwargs)
#             except Exception as e:
#                 # format the error message and traceback
#                 err_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                
#                 # create the email message
#                 message = MIMEText(err_msg)
#                 message['Subject'] = f"{func.__name__} failed"
#                 message['From'] = sender_email
#                 message['To'] = recipient_email
                
#                 # send the email
#                 with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
#                     smtp.login(sender_email, password)
#                     smtp.sendmail(sender_email, recipient_email, message.as_string())
                    
#                 # re-raise the exception
#                 raise
                
#         return wrapper
    
#     return decorator

# @email_on_failure(sender_email='your_email@gmail.com', password='your_password', recipient_email='recipient_email@gmail.com')
# def my_function():
#     # code that might fail
