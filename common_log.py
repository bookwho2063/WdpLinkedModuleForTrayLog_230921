# -*- coding: utf-8 -*-
#!/usr/bin/python

import logging
import logging.handlers
import time, os
import traceback

logger_path = "C:\\DrxSolution_WDP\\logs"
log_level = logging.INFO

# logs 폴더 존재여부 확인 및 미존재시 폴더 생성
try:
    if not os.path.exists(logger_path):
        os.makedirs(logger_path)
except OSError:
    print("logs 폴더 생성 실패 :: {}".format(traceback.format_exc()))


def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create TimedRotatingFileHandler
    time_handler = logging.handlers.TimedRotatingFileHandler(filename=logger_path + '\\linked_module_log_day_', when='midnight', interval=1, backupCount=30, encoding='utf-8')
    time_handler.setFormatter(formatter)
    logger.addHandler(time_handler)
    return logger

FILE_LOGGER = set_logger()

def log_info(message):
    FILE_LOGGER.info(message)

def log_warning(message):
    FILE_LOGGER.warning(message)

def log_error(message):
    FILE_LOGGER.error(message)

def log_debug(message):
    FILE_LOGGER.debug(message)





#
# def __init__(self, log_file_path, log_level=logging.DEBUG, max_log_size=102 4 *1024, backup_count=5):
#     self.log_file_path = log_file_path
#     self.log_level = log_level
#     self.max_log_size = max_log_size
#     self.backup_count = backup_count
#
#     # Create a console handler
#     # console_handler = logging.StreamHandler()
#     # console_handler.setFormatter(formatter)
#     # self.logger.addHandler(console_handler)
#
#     # Create a rotating file handler
#     # file_handler = RotatingFileHandler(log_file_path, maxBytes=max_log_size, backupCount=backup_count)
#     # file_handler.setFormatter(formatter)
#     # self.logger.addHandler(file_handler)
#
# def set_logger(self):
#     self.logger = logging.getLogger(__name__)
#     self.logger.setLevel(self.log_level)
#     self.check_logger()  # 로거 중복 방지
#
#     # Create a formatter
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
#     # Create TimedRotatingFileHandler
#     time_handler = logging.handlers.TimedRotatingFileHandler(filename=self.log_file_path + '_day_', when='midnight', interval=1, backupCount=30, encoding='utf-8')
#     time_handler.setFormatter(formatter)
#     self.logger.addHandler(time_handler)
#     # return self.logger
#
# def check_logger(self):
#     if len(self.logger.handlers) > 0:
#         return self.logger
#
# def log_info(self, message):
#     self.logger.info(message)
#
# def log_warning(self, message):
#     self.logger.warning(message)
#
# def log_error(self, message):
#     self.logger.error(message)
#
# def log_debug(self, message):
#     self.logger.debug(message)