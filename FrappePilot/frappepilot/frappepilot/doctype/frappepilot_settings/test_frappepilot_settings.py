# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import unittest

class TestFrappePilotSettings(unittest.TestCase):
	def test_settings_creation(self):
		"""Test that settings can be created and retrieved"""
		settings = frappe.get_single("FrappePilot Settings")
		self.assertIsNotNone(settings)
		self.assertEqual(settings.name, "FrappePilot Settings")
	
	def test_default_values(self):
		"""Test that default values are set correctly"""
		settings = frappe.get_single("FrappePilot Settings")
		self.assertEqual(settings.ollama_url, "http://localhost:11434")
		self.assertTrue(settings.enabled)

