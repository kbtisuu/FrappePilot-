# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AIUserPreference(Document):
	def validate(self):
		"""Validate the user preference"""
		if not self.user:
			frappe.throw("User is required")
		
		# Set default values if not provided
		if not self.response_verbosity:
			self.response_verbosity = "Normal"
		
		if not self.preferred_language:
			self.preferred_language = "English"
		
		if not self.max_conversation_history:
			self.max_conversation_history = 50
	
	def before_insert(self):
		"""Before insert operations"""
		# Check if preference already exists for this user
		existing = frappe.db.exists("AI User Preference", self.user)
		if existing:
			frappe.throw(f"Preference already exists for user {self.user}")
	
	@staticmethod
	def get_user_preference(user=None):
		"""Get user preference, create if doesn't exist"""
		if not user:
			user = frappe.session.user
		
		try:
			preference = frappe.get_doc("AI User Preference", user)
		except frappe.DoesNotExistError:
			# Create default preference
			preference = frappe.new_doc("AI User Preference")
			preference.user = user
			preference.response_verbosity = "Normal"
			preference.preferred_language = "English"
			preference.enable_notifications = 1
			preference.auto_save_conversations = 1
			preference.max_conversation_history = 50
			
			# Set default company if user has access to any
			companies = frappe.get_all("Company", limit=1)
			if companies:
				preference.default_company = companies[0].name
			
			preference.insert(ignore_permissions=True)
			frappe.db.commit()
		
		return preference
	
	@staticmethod
	def update_preference(user, field, value):
		"""Update a specific preference field for a user"""
		preference = AIUserPreference.get_user_preference(user)
		setattr(preference, field, value)
		preference.save(ignore_permissions=True)
		frappe.db.commit()
		
		return preference
	
	def get_conversation_context(self):
		"""Get conversation context based on user preferences"""
		context = {
			"verbosity": self.response_verbosity,
			"language": self.preferred_language,
			"company": self.default_company,
			"max_history": self.max_conversation_history
		}
		
		return context

