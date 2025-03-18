# core/util/log.py
# TODO: I don't know if it's worth creating a logger when django has one
# from enum import Enum
# from django.conf import settings
# import logging
# from datetime import datetime, timezone
#
# # This project tag gets added to every log message.
# PROJECT_TAG = "Depo"
#
#
# # TODO: Move to own module
# class SysMessages(Enum):
#     MISC_MSG = "Error occurred, don't know why."
#     BAD_FORMAT = "Invalid or unknown file/format type."
#     BAD_METHOD = "HTTP Method not allowed."
#     EMPTY_CONTENT = "Empty content provided."
#     TOO_LARGE = "File size exceeds limit."
#     SAVE_FAIL = "Error while saving content."
#
#     def __str__(self):
#         return self.value
#
#
# # TODO: Make this eventually inspect the stack for mod strings and using it in the log
# class DepoLogFormatter(logging.Formatter):
#     """
#     A basic formatter that logs the UTC timestamp in ISO8601 format,
#     the logging level, the project tag, and the log message.
#     This abstraction also allows us to easily swap in a 'rich' formatter later.
#     """
#     @classmethod
#     def create_logger(cls, name=PROJECT_TAG):
#         logger = logging.getLogger(name)
#         logger.setLevel(settings.LOG_LEVEL)
#         ch = logging.StreamHandler()
#         ch.setLevel(logging.DEBUG)
#         formatter = cls()
#         ch.setFormatter(formatter)
#         logger.addHandler(ch)
#         return logger
#
#     def formatTime(self, record, datefmt=None):
#         # Create a UTC datetime from record.created and format as ISO8601.
#         ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
#         return ct.isoformat()
#
#     def format(self, record):
#         record.message = record.getMessage()
#         timestamp = self.formatTime(record)
#         # Format: "<timestamp> [<LEVEL>] <PROJECT_TAG> - <message>"
#         formatted = f"{timestamp} [{record.levelname}] {PROJECT_TAG} - {record.message}"
#         return formatted
#
#
# # Create and configure the centralized logger.
# logger = logging.getLogger("centralizedLogger")
# logger.setLevel(logging.DEBUG)  # Accept all log levels
#
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# formatter = BasicLogFormatter()
# ch.setFormatter(formatter)
# logger.addHandler(ch)
#
#
# def log_debug(message):
#     """Log a message with DEBUG level."""
#     logger.debug(message)
#
#
# def log_info(message):
#     """Log a message with INFO level."""
#     logger.info(message)
#
#
# def log_warning(message):
#     """Log a message with WARNING level."""
#     logger.warning(message)
#
#
# def log_error(message):
#     """Log a message with ERROR level."""
#     logger.error(message)
#
#
# def log_critical(message):
#     """Log a message with CRITICAL level."""
#     logger.critical(message)
