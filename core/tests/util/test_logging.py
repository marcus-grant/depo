# core/tests/util/test_logging.py

import importlib
from django.test import TestCase

import core.util.logging as log


class LoggingUtilTests(TestCase):
    """Tests for core.util.logging"""

    def test_project_tag(self):
        """Ensure project tag is correct."""
        self.assertEqual(log.PROJECT_TAG, "DEPO")

    def test_logger_is_standard_logger(self):
        """Ensure that the class name is DepoLogger and is importable as such"""
        # Import the module and class
        module = importlib.import_module("core.util.logging")
        # Check if module imports with name and see if class exists
        self.assertTrue(hasattr(module, "DepoLogger"))
        logger_class = getattr(module, "DepoLogger")
        # Check if class name correct
        self.assertEqual(logger_class.__name__, "DepoLogger")
