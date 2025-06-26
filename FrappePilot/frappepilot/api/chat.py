# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import time
import json
from frappepilot.services.ollama_service import ollama_service
from frappepilot.services.rbac_service import rbac_service
from frappepilot.frappepilot.doctype.ai_command_log.ai_command_log import AICommandLog
from frappepilot.frappepilot.doctype.ai_user_preference.ai_user_preference import AIUserPreference
from frappepilot.services.action_executor import action_executor
from frappepilot.services.error_handler import error_handler
from frappepilot.services.security_validator import security_validator

@frappe.whitelist()
def check_status():
	"""Check if FrappePilot is online and ready"""
	try:
		# Validate user permissions
		is_valid, message = security_validator.validate_user_permissions()
		if not is_valid:
			return {"status": "error", "message": message}
		
		# Check rate limit
		within_limit, limit_message = security_validator.check_rate_limit(action="status_check", limit=60, window=60)
		if not within_limit:
			return {"status": "error", "message": limit_message}
		
		# Check if Ollama is available
		if ollama_service.is_available():
			return {"status": "online", "message": "FrappePilot is ready"}
		else:
			return {"status": "offline", "message": "Ollama service is not available"}
	except Exception as e:
		error_message = error_handler.handle_error(e, "checking FrappePilot status")
		return {"status": "error", "message": error_message}

@frappe.whitelist()
def process_message(message):
	"""Process a user message and return AI response"""
	start_time = time.time()
	
	try:
		# Validate user permissions
		is_valid, validation_message = security_validator.validate_user_permissions()
		if not is_valid:
			security_validator.log_security_event("invalid_user_access", {"message": validation_message})
			return {
				"success": False,
				"response": "Access denied",
				"error": validation_message,
				"action_executed": None
			}
		
		# Check rate limit
		within_limit, limit_message = security_validator.check_rate_limit(action="message_processing", limit=30, window=60)
		if not within_limit:
			security_validator.log_security_event("rate_limit_exceeded", {"limit_message": limit_message})
			return {
				"success": False,
				"response": "Too many requests. Please wait before sending another message.",
				"error": limit_message,
				"action_executed": None
			}
		
		# Sanitize input
		sanitized_message = security_validator.sanitize_input(message)
		if not sanitized_message:
			return {
				"success": False,
				"response": "Please provide a valid message.",
				"error": "Empty or invalid message",
				"action_executed": None
			}
		
		# Create command log
		log = AICommandLog.create_log(sanitized_message)
		
		# Get user preferences
		user_preference = AIUserPreference.get_user_preference()
		
		# Extract intent and entities using Ollama
		intent_data = ollama_service.extract_intent_and_entities(sanitized_message)
		log.update_intent_and_entities(intent_data.get("intent"), intent_data.get("entities"))
		
		# Check permissions for the intent
		can_execute, permission_message = rbac_service.check_permission(intent_data.get("intent"))
		
		if not can_execute:
			# Permission denied
			response = f"I'm sorry, but you don't have permission to perform this action. {permission_message}"
			log.update_status("Denied", response)
			log.set_execution_time(start_time)
			
			security_validator.log_security_event("permission_denied", {
				"intent": intent_data.get("intent"),
				"message": permission_message
			})
			
			return {
				"success": False,
				"response": response,
				"error": permission_message,
				"action_executed": None
			}
		
		# Execute the action
		try:
			action_result = action_executor.execute_action(
				intent_data.get("intent"),
				intent_data.get("entities", {}),
				user_preference
			)
			
			if action_result.get("success"):
				# Generate response using Ollama
				context = f"Action executed successfully: {action_result.get('message', '')}"
				if action_result.get("data"):
					context += f"\nData: {json.dumps(action_result['data'], indent=2)}"
				
				ai_response = ollama_service.generate_response(
					f"Summarize this action result for the user: {context}",
					context
				)
				
				log.update_action_executed(action_result.get("action_name"))
				log.update_status("Success", ai_response)
				log.set_execution_time(start_time)
				
				return {
					"success": True,
					"response": ai_response,
					"action_executed": action_result.get("action_name"),
					"data": action_result.get("data")
				}
			else:
				# Action failed
				error_message = action_result.get("error", "Action execution failed")
				ai_response = f"I encountered an error while executing your request: {error_message}"
				
				log.update_status("Failed", ai_response, error_message)
				log.set_execution_time(start_time)
				
				return {
					"success": False,
					"response": ai_response,
					"error": error_message,
					"action_executed": None
				}
				
		except Exception as action_error:
			# Action execution error
			error_message = error_handler.handle_error(action_error, "executing action")
			ai_response = f"I encountered an error while processing your request: {error_message}"
			
			log.update_status("Failed", ai_response, error_message)
			log.set_execution_time(start_time)
			
			return {
				"success": False,
				"response": ai_response,
				"error": error_message,
				"action_executed": None
			}
	
	except Exception as e:
		# General error
		error_message = error_handler.handle_error(e, "processing message")
		
		return {
			"success": False,
			"response": "I'm sorry, I encountered an unexpected error. Please try again.",
			"error": error_message,
			"action_executed": None
		}

@frappe.whitelist()
def get_conversation_history(limit=10):
	"""Get conversation history for the current user"""
	try:
		# Validate user permissions
		is_valid, message = security_validator.validate_user_permissions()
		if not is_valid:
			return []
		
		# Validate limit
		try:
			limit = int(limit)
			if limit < 1 or limit > 100:
				limit = 10
		except (ValueError, TypeError):
			limit = 10
		
		logs = AICommandLog.get_user_logs(limit=limit)
		return logs
	except Exception as e:
		error_handler.handle_error(e, "getting conversation history")
		return []

@frappe.whitelist()
def get_user_permissions():
	"""Get user permissions and available actions"""
	try:
		# Validate user permissions
		is_valid, message = security_validator.validate_user_permissions()
		if not is_valid:
			return {"roles": [], "available_actions": [], "is_system_manager": False}
		
		permissions = rbac_service.get_user_permissions()
		return permissions
	except Exception as e:
		error_handler.handle_error(e, "getting user permissions")
		return {"roles": [], "available_actions": [], "is_system_manager": False}

@frappe.whitelist()
def update_user_preference(field, value):
	"""Update user preference"""
	try:
		# Validate user permissions
		is_valid, message = security_validator.validate_user_permissions()
		if not is_valid:
			return {"success": False, "error": message}
		
		# Sanitize inputs
		field = security_validator.sanitize_input(field)
		value = security_validator.sanitize_input(value)
		
		# Validate field name
		allowed_fields = ["response_verbosity", "preferred_language", "enable_notifications", 
						 "auto_save_conversations", "max_conversation_history", "default_company"]
		
		if field not in allowed_fields:
			return {"success": False, "error": "Invalid field name"}
		
		preference = AIUserPreference.update_preference(frappe.session.user, field, value)
		return {"success": True, "message": "Preference updated successfully"}
	except Exception as e:
		error_message = error_handler.handle_error(e, "updating user preference")
		return {"success": False, "error": error_message}

