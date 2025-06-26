# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import re
from frappepilot.frappepilot.doctype.frappepilot_settings.frappepilot_settings import FrappePilotSettings

class OllamaService:
	"""Service class for interacting with Ollama"""
	
	def __init__(self):
		self.settings = FrappePilotSettings.get_settings()
		self.base_url = self.settings.ollama_url.rstrip('/')
	
	def is_available(self):
		"""Check if Ollama is available"""
		try:
			response = requests.get(f"{self.base_url}/api/tags", timeout=5)
			return response.status_code == 200
		except:
			return False
	
	def generate_response(self, prompt, context=None):
		"""Generate response from Ollama"""
		if not self.settings.enabled:
			raise Exception("FrappePilot is disabled")
		
		if not self.is_available():
			raise Exception("Ollama service is not available")
		
		# Prepare the full prompt with system context
		full_prompt = self._prepare_prompt(prompt, context)
		
		try:
			payload = {
				"model": self.settings.active_model,
				"prompt": full_prompt,
				"stream": False,
				"options": {
					"temperature": self.settings.temperature,
					"num_predict": self.settings.max_tokens
				}
			}
			
			response = requests.post(
				f"{self.base_url}/api/generate",
				json=payload,
				timeout=60
			)
			
			if response.status_code == 200:
				result = response.json()
				return result.get("response", "")
			else:
				raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
				
		except requests.exceptions.RequestException as e:
			raise Exception(f"Failed to connect to Ollama: {str(e)}")
	
	def extract_intent_and_entities(self, user_input):
		"""Extract intent and entities from user input using Ollama"""
		
		# Craft a specific prompt for intent and entity extraction
		extraction_prompt = f"""
You are an AI assistant that extracts intent and entities from user queries for an ERPNext system.

Analyze the following user input and extract:
1. Intent: The main action the user wants to perform
2. Entities: Specific data mentioned (names, dates, amounts, etc.)

User Input: "{user_input}"

Respond ONLY with a valid JSON object in this exact format:
{{
  "intent": "action_name",
  "entities": {{
    "entity_type": "entity_value"
  }},
  "confidence": 0.95
}}

Common intents include:
- create_sales_order
- get_stock_levels
- create_item
- get_customer_info
- create_customer
- get_sales_report
- create_warehouse
- update_item_price
- get_outstanding_invoices

Example entities:
- customer_name, item_name, quantity, price, date, warehouse_name, etc.
"""
		
		try:
			response = self.generate_response(extraction_prompt)
			
			# Try to extract JSON from the response
			json_match = re.search(r'\{.*\}', response, re.DOTALL)
			if json_match:
				json_str = json_match.group()
				return json.loads(json_str)
			else:
				# Fallback parsing
				return self._fallback_intent_extraction(user_input)
				
		except Exception as e:
			frappe.log_error(f"Intent extraction error: {str(e)}")
			return self._fallback_intent_extraction(user_input)
	
	def _prepare_prompt(self, user_prompt, context=None):
		"""Prepare the full prompt with system context"""
		system_prompt = self.settings.system_prompt or "You are FrappePilot, an intelligent AI assistant for ERPNext."
		
		full_prompt = f"{system_prompt}\n\n"
		
		if context:
			full_prompt += f"Context: {context}\n\n"
		
		full_prompt += f"User: {user_prompt}\n\nAssistant:"
		
		return full_prompt
	
	def _fallback_intent_extraction(self, user_input):
		"""Fallback intent extraction using simple keyword matching"""
		user_input_lower = user_input.lower()
		
		# Simple keyword-based intent detection
		if any(word in user_input_lower for word in ["create", "add", "new"]):
			if "sales order" in user_input_lower:
				intent = "create_sales_order"
			elif "customer" in user_input_lower:
				intent = "create_customer"
			elif "item" in user_input_lower:
				intent = "create_item"
			elif "warehouse" in user_input_lower:
				intent = "create_warehouse"
			else:
				intent = "create_document"
		elif any(word in user_input_lower for word in ["get", "show", "list", "find"]):
			if "stock" in user_input_lower:
				intent = "get_stock_levels"
			elif "customer" in user_input_lower:
				intent = "get_customer_info"
			elif "report" in user_input_lower:
				intent = "get_sales_report"
			else:
				intent = "get_information"
		else:
			intent = "general_query"
		
		return {
			"intent": intent,
			"entities": {},
			"confidence": 0.5
		}

# Global instance
ollama_service = OllamaService()

