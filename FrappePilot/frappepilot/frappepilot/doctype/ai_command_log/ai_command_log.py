# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
import time

class AICommandLog(Document):
	def validate(self):
		"""Validate the command log"""
		if not self.user:
			self.user = frappe.session.user
		
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
	
	def before_insert(self):
		"""Before insert operations"""
		# Ensure user is set
		if not self.user:
			self.user = frappe.session.user
	
	@staticmethod
	def create_log(user_input, user=None):
		"""Create a new command log entry"""
		if not user:
			user = frappe.session.user
		
		log = frappe.new_doc("AI Command Log")
		log.user = user
		log.user_input = user_input
		log.timestamp = frappe.utils.now()
		log.status = "Processing"
		log.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return log
	
	def update_intent_and_entities(self, intent, entities):
		"""Update the log with extracted intent and entities"""
		self.intent = intent
		self.entities = json.dumps(entities) if entities else None
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	def update_action_executed(self, action_name):
		"""Update the log with the action that was executed"""
		self.action_executed = action_name
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	def update_status(self, status, response=None, error_message=None):
		"""Update the log status and response"""
		self.status = status
		
		if response:
			self.assistant_response = response
		
		if error_message:
			self.error_message = error_message
		
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	def update_ollama_interaction(self, prompt, response):
		"""Update the log with Ollama prompt and response"""
		self.ollama_prompt = prompt
		self.ollama_response = response
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	def set_execution_time(self, start_time):
		"""Set the execution time based on start time"""
		self.execution_time = time.time() - start_time
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	@staticmethod
	def get_user_logs(user=None, limit=50):
		"""Get command logs for a user"""
		if not user:
			user = frappe.session.user
		
		logs = frappe.get_all(
			"AI Command Log",
			filters={"user": user},
			fields=["name", "timestamp", "user_input", "intent", "status", "assistant_response"],
			order_by="timestamp desc",
			limit=limit
		)
		
		return logs
	
	@staticmethod
	def get_system_logs(limit=100):
		"""Get system-wide command logs (System Manager only)"""
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Managers can view system logs")
		
		logs = frappe.get_all(
			"AI Command Log",
			fields=["name", "user", "timestamp", "user_input", "intent", "status", "assistant_response", "error_message"],
			order_by="timestamp desc",
			limit=limit
		)
		
		return logs
	
	@staticmethod
	def get_analytics():
		"""Get analytics data for command logs (System Manager only)"""
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Managers can view analytics")
		
		# Get total commands
		total_commands = frappe.db.count("AI Command Log")
		
		# Get commands by status
		status_counts = frappe.db.sql("""
			SELECT status, COUNT(*) as count
			FROM `tabAI Command Log`
			GROUP BY status
		""", as_dict=True)
		
		# Get top intents
		intent_counts = frappe.db.sql("""
			SELECT intent, COUNT(*) as count
			FROM `tabAI Command Log`
			WHERE intent IS NOT NULL
			GROUP BY intent
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		# Get top users
		user_counts = frappe.db.sql("""
			SELECT user, COUNT(*) as count
			FROM `tabAI Command Log`
			GROUP BY user
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		# Get average execution time
		avg_execution_time = frappe.db.sql("""
			SELECT AVG(execution_time) as avg_time
			FROM `tabAI Command Log`
			WHERE execution_time IS NOT NULL
		""", as_dict=True)
		
		return {
			"total_commands": total_commands,
			"status_counts": status_counts,
			"intent_counts": intent_counts,
			"user_counts": user_counts,
			"avg_execution_time": avg_execution_time[0].avg_time if avg_execution_time else 0
		}

