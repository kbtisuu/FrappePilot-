# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FrappePilotSettings(Document):
	def validate(self):
		"""Validate the settings"""
		if not self.ollama_url:
			frappe.throw("Ollama URL is required")
		
		if not self.active_model:
			frappe.throw("Active Model is required")
		
		# Ensure only one settings document exists
		if not self.name:
			self.name = "FrappePilot Settings"
	
	def on_update(self):
		"""Clear cache when settings are updated"""
		frappe.cache().delete_value("frappepilot_settings")
	
	@staticmethod
	def get_settings():
		"""Get FrappePilot settings"""
		settings = frappe.cache().get_value("frappepilot_settings")
		if not settings:
			try:
				settings = frappe.get_single("FrappePilot Settings")
				frappe.cache().set_value("frappepilot_settings", settings)
			except frappe.DoesNotExistError:
				# Create default settings if they don't exist
				settings = frappe.new_doc("FrappePilot Settings")
				settings.name = "FrappePilot Settings"
				settings.ollama_url = "http://localhost:11434"
				settings.active_model = "phi3:3.8b-mini"
				settings.max_tokens = 1000
				settings.temperature = 0.7
				settings.system_prompt = "You are FrappePilot, an intelligent AI assistant for ERPNext. Help users with their ERPNext tasks while respecting their role-based permissions."
				settings.enabled = 1
				settings.insert(ignore_permissions=True)
				frappe.cache().set_value("frappepilot_settings", settings)
		
		return settings

