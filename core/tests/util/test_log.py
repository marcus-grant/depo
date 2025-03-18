# core/tests/util/test_log.py
# TODO: I don't know if a logger is necessary when Django has one
# import re
# import unittest
# from django.test import TestCase
# from core.util import log
#
#
# class LoggingUtilTests(TestCase):
#     def test_project_tag(self):
#         self.assertEqual(log.PROJECT_TAG, "DEPO")
#
#     def test_logger_name(self):
#         logger = log.get_logger()
#         # The logger should always be named "core.util.logging"
#         self.assertEqual(logger.name, "core.util.logging")
#
#     def test_log_levels(self):
#         with self.assertLogs("core.util.logging", level="DEBUG") as cm:
#             log.DepoLogger.log_debug("Test debug")
#             log.DepoLogger.log_info("Test info")
#             log.DepoLogger.log_warning("Test warning")
#             log.DepoLogger.log_error("Test error")
#             log.DepoLogger.log_critical("Test critical")
#         self.assertGreaterEqual(len(cm.output), 5, "Expected at least 5 log messages")
#
#     def test_iso8601_timestamp_format(self):
#         with self.assertLogs("core.util.logging", level="DEBUG") as cm:
#             log.DepoLogger.log_info("Test timestamp")
#         log_line = cm.output[0]
#         # Expect a timestamp at the start
#         timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
#         self.assertRegex(
#             log_line, timestamp_pattern, "Timestamp format doesn't match ISO8601."
#         )
#
#     def test_project_tag_in_logs(self):
#         with self.assertLogs("core.util.logging", level="DEBUG") as cm:
#             log.DepoLogger.log_info("Test project tag")
#         log_line = cm.output[0]
#         self.assertIn(
#             f"[{log.PROJECT_TAG}]", log_line, "Expected project tag in log message"
#         )
#
#     def test_sys_messages_importability(self):
#         from core.util.log import SysMessages
#
#         self.assertTrue(
#             hasattr(SysMessages, "MISC_MSG"), "SysMessages missing MISC_MSG"
#         )
#
#
# if __name__ == "__main__":
#     unittest.main()
