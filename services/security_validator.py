# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import re
import html
import json
from urllib.parse import urlparse

class SecurityValidator:
	"""Security validation service for FrappePilot"""
	
	@staticmethod
	def sanitize_input(input_text):
		"""Sanitize user input to prevent injection attacks"""
		if not input_text:
			return ""
		
		# Convert to string if not already
		input_text = str(input_text)
		
		# HTML escape
		input_text = html.escape(input_text)
		
		# Remove potentially dangerous characters
		dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
		for char in dangerous_chars:
			input_text = input_text.replace(char, '')
		
		# Limit length
		if len(input_text) > 10000:
			input_text = input_text[:10000]
		
		return input_text.strip()
	
	@staticmethod
	def validate_command(command):
		"""Validate bench commands for security"""
		if not command:
			return False, "Command cannot be empty"
		
		# Whitelist of allowed commands
		allowed_commands = [
			"bench version",
			"bench status", 
			"bench restart",
			"bench update",
			"bench migrate",
			"bench build",
			"bench --help"
		]
		
		# Check if command is in whitelist
		if command not in allowed_commands:
			return False, f"Command '{command}' is not allowed"
		
		# Additional security checks
		dangerous_patterns = [
			r'[;&|`$()]',  # Shell metacharacters
			r'\.\./',      # Directory traversal
			r'rm\s',       # Delete commands
			r'sudo\s',     # Privilege escalation
			r'chmod\s',    # Permission changes
			r'>/dev/',     # Device access
		]
		
		for pattern in dangerous_patterns:
			if re.search(pattern, command, re.IGNORECASE):
				return False, "Command contains potentially dangerous characters"
		
		return True, "Command is valid"
	
	@staticmethod
	def validate_model_name(model_name):
		"""Validate Ollama model names"""
		if not model_name:
			return False, "Model name cannot be empty"
		
		# Allow only alphanumeric, hyphens, underscores, colons, and dots
		if not re.match(r'^[a-zA-Z0-9\-_:.]+$', model_name):
			return False, "Model name contains invalid characters"
		
		# Prevent directory traversal
		if '..' in model_name or '/' in model_name:
			return False, "Model name cannot contain path separators"
		
		# Length limit
		if len(model_name) > 100:
			return False, "Model name is too long"
		
		return True, "Model name is valid"
	
	@staticmethod
	def validate_json_input(json_str):
		"""Validate and sanitize JSON input"""
		try:
			# Parse JSON
			data = json.loads(json_str)
			
			# Recursively sanitize all string values
			def sanitize_json_values(obj):
				if isinstance(obj, dict):
					return {k: sanitize_json_values(v) for k, v in obj.items()}
				elif isinstance(obj, list):
					return [sanitize_json_values(item) for item in obj]
				elif isinstance(obj, str):
					return SecurityValidator.sanitize_input(obj)
				else:
					return obj
			
			sanitized_data = sanitize_json_values(data)
			return True, sanitized_data
			
		except json.JSONDecodeError as e:
			return False, f"Invalid JSON: {str(e)}"
	
	@staticmethod
	def validate_url(url):
		"""Validate URLs for Ollama connections"""
		if not url:
			return False, "URL cannot be empty"
		
		try:
			parsed = urlparse(url)
			
			# Check scheme
			if parsed.scheme not in ['http', 'https']:
				return False, "URL must use http or https protocol"
			
			# Check hostname
			if not parsed.hostname:
				return False, "URL must have a valid hostname"
			
			# Prevent access to internal networks (basic check)
			hostname = parsed.hostname.lower()
			if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
				# Allow localhost for development
				pass
			elif hostname.startswith('192.168.') or hostname.startswith('10.') or hostname.startswith('172.'):
				# Allow private networks
				pass
			elif hostname.startswith('169.254.'):
				return False, "Access to link-local addresses is not allowed"
			
			# Check port range
			if parsed.port and (parsed.port < 1 or parsed.port > 65535):
				return False, "Invalid port number"
			
			return True, "URL is valid"
			
		except Exception as e:
			return False, f"Invalid URL: {str(e)}"
	
	@staticmethod
	def validate_file_path(file_path):
		"""Validate file paths to prevent directory traversal"""
		if not file_path:
			return False, "File path cannot be empty"
		
		# Normalize path
		import os
		normalized_path = os.path.normpath(file_path)
		
		# Check for directory traversal
		if '..' in normalized_path:
			return False, "Directory traversal is not allowed"
		
		# Check for absolute paths (should be relative)
		if os.path.isabs(normalized_path):
			return False, "Absolute paths are not allowed"
		
		# Check for dangerous characters
		dangerous_chars = ['<', '>', '|', '&', ';', '`', '$']
		for char in dangerous_chars:
			if char in file_path:
				return False, f"File path contains dangerous character: {char}"
		
		return True, "File path is valid"
	
	@staticmethod
	def check_rate_limit(user=None, action="api_call", limit=100, window=3600):
		"""Basic rate limiting check"""
		if not user:
			user = frappe.session.user
		
		# Get current time
		import time
		current_time = int(time.time())
		window_start = current_time - window
		
		# Create cache key
		cache_key = f"rate_limit:{user}:{action}:{window_start // window}"
		
		# Get current count
		current_count = frappe.cache().get_value(cache_key) or 0
		
		if current_count >= limit:
			return False, f"Rate limit exceeded. Maximum {limit} {action}s per {window} seconds"
		
		# Increment count
		frappe.cache().set_value(cache_key, current_count + 1, expires_in_sec=window)
		
		return True, "Within rate limit"
	
	@staticmethod
	def validate_user_permissions(user=None):
		"""Validate user permissions and session"""
		if not user:
			user = frappe.session.user
		
		# Check if user exists and is enabled
		if not frappe.db.exists("User", user):
			return False, "User does not exist"
		
		user_doc = frappe.get_doc("User", user)
		if user_doc.enabled != 1:
			return False, "User account is disabled"
		
		# Check session validity
		if not frappe.session.user or frappe.session.user == "Guest":
			return False, "Invalid session"
		
		return True, "User permissions valid"
	
	@staticmethod
	def log_security_event(event_type, details, user=None):
		"""Log security events for monitoring"""
		if not user:
			user = frappe.session.user
		
		try:
			# Create a security log entry
			security_log = {
				"doctype": "Error Log",
				"method": f"FrappePilot Security Event: {event_type}",
				"error": json.dumps({
					"event_type": event_type,
					"details": details,
					"user": user,
					"timestamp": frappe.utils.now(),
					"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else None
				}, indent=2)
			}
			
			frappe.get_doc(security_log).insert(ignore_permissions=True)
			frappe.db.commit()
			
		except Exception as e:
			# Don't let logging errors break the main flow
			print(f"Failed to log security event: {str(e)}")

# Global security validator instance
security_validator = SecurityValidator()

