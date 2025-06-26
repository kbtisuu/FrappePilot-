# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AIActionDefinition(Document):
	def validate(self):
		"""Validate the action definition"""
		if not self.action_name:
			frappe.throw("Action Name is required")
		
		if not self.display_name:
			self.display_name = self.action_name
		
		if not self.intent:
			frappe.throw("Intent is required")
		
		if not self.function_name:
			frappe.throw("Function Name is required")
	
	def can_user_execute(self, user=None):
		"""Check if a user can execute this action"""
		if not user:
			user = frappe.session.user
		
		if not self.enabled:
			return False, "Action is disabled"
		
		# Get user roles
		user_roles = frappe.get_roles(user)
		
		# If action is admin only, check for System Manager role
		if self.is_admin_only:
			if "System Manager" not in user_roles:
				return False, "This action requires System Manager role"
		
		# Check required roles
		if self.required_roles:
			required_role_names = [role.role for role in self.required_roles]
			
			# Check if user has any of the required roles
			has_required_role = any(role in user_roles for role in required_role_names)
			
			if not has_required_role:
				return False, f"This action requires one of these roles: {', '.join(required_role_names)}"
		
		return True, "Authorized"
	
	@staticmethod
	def get_action_by_intent(intent):
		"""Get action definition by intent"""
		actions = frappe.get_all(
			"AI Action Definition",
			filters={"intent": intent, "enabled": 1},
			fields=["name", "action_name", "display_name", "function_name", "is_admin_only"]
		)
		
		if actions:
			return frappe.get_doc("AI Action Definition", actions[0].name)
		
		return None
	
	@staticmethod
	def get_available_actions_for_user(user=None):
		"""Get all actions available for a user"""
		if not user:
			user = frappe.session.user
		
		user_roles = frappe.get_roles(user)
		available_actions = []
		
		# Get all enabled actions
		actions = frappe.get_all(
			"AI Action Definition",
			filters={"enabled": 1},
			fields=["name"]
		)
		
		for action in actions:
			action_doc = frappe.get_doc("AI Action Definition", action.name)
			can_execute, message = action_doc.can_user_execute(user)
			
			if can_execute:
				available_actions.append({
					"action_name": action_doc.action_name,
					"display_name": action_doc.display_name,
					"description": action_doc.description,
					"intent": action_doc.intent
				})
		
		return available_actions

