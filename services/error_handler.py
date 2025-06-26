# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import traceback
import sys
from datetime import datetime

class ErrorHandler:
	"""Centralized error handling for FrappePilot"""
	
	@staticmethod
	def handle_error(error, context="", user_friendly=True):
		"""Handle and log errors with appropriate user feedback"""
		
		# Log the full error details
		error_details = {
			"error": str(error),
			"context": context,
			"traceback": traceback.format_exc(),
			"timestamp": datetime.now().isoformat(),
			"user": frappe.session.user,
			"method": frappe.local.form_dict.cmd if hasattr(frappe.local, 'form_dict') else None
		}
		
		# Log to Frappe error log
		frappe.log_error(
			message=f"FrappePilot Error: {str(error)}\nContext: {context}\nTraceback: {traceback.format_exc()}",
			title="FrappePilot Error"
		)
		
		# Return user-friendly error message
		if user_friendly:
			return ErrorHandler.get_user_friendly_message(error, context)
		else:
			return str(error)
	
	@staticmethod
	def get_user_friendly_message(error, context=""):
		"""Convert technical errors to user-friendly messages"""
		
		error_str = str(error).lower()
		
		# Database errors
		if "duplicate entry" in error_str:
			return "This record already exists. Please check your input and try again."
		
		if "foreign key constraint" in error_str:
			return "This action cannot be completed because it would affect related records."
		
		if "table doesn't exist" in error_str or "column doesn't exist" in error_str:
			return "There seems to be a system configuration issue. Please contact your administrator."
		
		# Permission errors
		if "permission" in error_str or "not allowed" in error_str:
			return "You don't have permission to perform this action. Please contact your administrator if you believe this is an error."
		
		# Validation errors
		if "required" in error_str or "mandatory" in error_str:
			return "Some required information is missing. Please provide all necessary details and try again."
		
		# Network/connection errors
		if "connection" in error_str or "timeout" in error_str or "network" in error_str:
			return "There was a connection issue. Please check your network and try again."
		
		# Ollama specific errors
		if "ollama" in error_str:
			if "not available" in error_str or "connection refused" in error_str:
				return "The AI service is currently unavailable. Please try again later or contact your administrator."
			elif "model not found" in error_str:
				return "The AI model is not available. Please contact your administrator to configure the AI models."
		
		# File/resource errors
		if "file not found" in error_str or "no such file" in error_str:
			return "A required file or resource could not be found. Please contact your administrator."
		
		# Generic errors
		if context:
			return f"An error occurred while {context}. Please try again or contact support if the problem persists."
		else:
			return "An unexpected error occurred. Please try again or contact support if the problem persists."
	
	@staticmethod
	def validate_input(data, required_fields, field_types=None):
		"""Validate input data and return user-friendly error messages"""
		
		errors = []
		
		# Check required fields
		for field in required_fields:
			if field not in data or not data[field]:
				errors.append(f"{field.replace('_', ' ').title()} is required")
		
		# Check field types if specified
		if field_types:
			for field, expected_type in field_types.items():
				if field in data and data[field] is not None:
					if expected_type == "email":
						if "@" not in str(data[field]) or "." not in str(data[field]):
							errors.append(f"{field.replace('_', ' ').title()} must be a valid email address")
					elif expected_type == "number":
						try:
							float(data[field])
						except (ValueError, TypeError):
							errors.append(f"{field.replace('_', ' ').title()} must be a number")
					elif expected_type == "positive_number":
						try:
							if float(data[field]) <= 0:
								errors.append(f"{field.replace('_', ' ').title()} must be a positive number")
						except (ValueError, TypeError):
							errors.append(f"{field.replace('_', ' ').title()} must be a positive number")
		
		return errors
	
	@staticmethod
	def safe_execute(func, *args, **kwargs):
		"""Safely execute a function with error handling"""
		try:
			return {
				"success": True,
				"result": func(*args, **kwargs),
				"error": None
			}
		except Exception as e:
			error_message = ErrorHandler.handle_error(e, f"executing {func.__name__}")
			return {
				"success": False,
				"result": None,
				"error": error_message
			}
	
	@staticmethod
	def wrap_api_response(func):
		"""Decorator to wrap API responses with error handling"""
		def wrapper(*args, **kwargs):
			try:
				result = func(*args, **kwargs)
				return result
			except Exception as e:
				error_message = ErrorHandler.handle_error(e, f"API call to {func.__name__}")
				return {
					"success": False,
					"error": error_message,
					"data": None
				}
		return wrapper

# Global error handler instance
error_handler = ErrorHandler()

