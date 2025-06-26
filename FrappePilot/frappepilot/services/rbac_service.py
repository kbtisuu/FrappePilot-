# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappepilot.frappepilot.doctype.ai_action_definition.ai_action_definition import AIActionDefinition

class RBACService:
	"""Service class for Role-Based Access Control"""
	
	@staticmethod
	def check_permission(intent, user=None):
		"""Check if user has permission to execute an action based on intent"""
		if not user:
			user = frappe.session.user
		
		# Get action definition for the intent
		action = AIActionDefinition.get_action_by_intent(intent)
		
		if not action:
			return False, f"No action defined for intent: {intent}"
		
		# Check if user can execute this action
		can_execute, message = action.can_user_execute(user)
		
		return can_execute, message
	
	@staticmethod
	def get_user_permissions(user=None):
		"""Get all permissions for a user"""
		if not user:
			user = frappe.session.user
		
		user_roles = frappe.get_roles(user)
		permissions = {
			"roles": user_roles,
			"available_actions": AIActionDefinition.get_available_actions_for_user(user),
			"is_system_manager": "System Manager" in user_roles
		}
		
		return permissions
	
	@staticmethod
	def validate_erpnext_permission(doctype, action, user=None):
		"""Validate ERPNext permission for a specific doctype and action"""
		if not user:
			user = frappe.session.user
		
		# Use Frappe's built-in permission system
		try:
			if action == "read":
				return frappe.has_permission(doctype, "read", user=user)
			elif action == "write":
				return frappe.has_permission(doctype, "write", user=user)
			elif action == "create":
				return frappe.has_permission(doctype, "create", user=user)
			elif action == "delete":
				return frappe.has_permission(doctype, "delete", user=user)
			else:
				return False
		except:
			return False
	
	@staticmethod
	def get_accessible_doctypes(user=None):
		"""Get all doctypes accessible to a user"""
		if not user:
			user = frappe.session.user
		
		accessible_doctypes = []
		
		# Get all doctypes
		all_doctypes = frappe.get_all("DocType", fields=["name", "module"])
		
		for doctype in all_doctypes:
			if frappe.has_permission(doctype.name, "read", user=user):
				accessible_doctypes.append({
					"doctype": doctype.name,
					"module": doctype.module,
					"can_read": True,
					"can_write": frappe.has_permission(doctype.name, "write", user=user),
					"can_create": frappe.has_permission(doctype.name, "create", user=user),
					"can_delete": frappe.has_permission(doctype.name, "delete", user=user)
				})
		
		return accessible_doctypes

# Global instance
rbac_service = RBACService()

