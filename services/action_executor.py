# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
import subprocess
import json
import re
from frappepilot.frappepilot.doctype.ai_action_definition.ai_action_definition import AIActionDefinition
from frappepilot.services.rbac_service import rbac_service

class ActionExecutor:
	"""Service class for executing AI actions"""
	
	def __init__(self):
		self.action_map = {
			"create_sales_order": self.create_sales_order,
			"get_stock_levels": self.get_stock_levels,
			"create_item": self.create_item,
			"get_customer_info": self.get_customer_info,
			"create_customer": self.create_customer,
			"get_sales_report": self.get_sales_report,
			"create_warehouse": self.create_warehouse,
			"update_item_price": self.update_item_price,
			"get_outstanding_invoices": self.get_outstanding_invoices,
			"manage_ollama_models": self.manage_ollama_models,
			"run_bench_command": self.run_bench_command,
			"create_user": self.create_user,
			"general_query": self.general_query
		}
	
	def execute_action(self, intent, entities, user_preference):
		"""Execute an action based on intent and entities"""
		try:
			# Get action definition
			action_def = AIActionDefinition.get_action_by_intent(intent)
			
			if not action_def:
				return {
					"success": False,
					"error": f"No action defined for intent: {intent}",
					"action_name": None
				}
			
			# Check permissions again (double-check)
			can_execute, message = action_def.can_user_execute()
			if not can_execute:
				return {
					"success": False,
					"error": message,
					"action_name": action_def.action_name
				}
			
			# Get the action function
			action_function = self.action_map.get(intent)
			
			if not action_function:
				return {
					"success": False,
					"error": f"Action function not implemented for intent: {intent}",
					"action_name": action_def.action_name
				}
			
			# Execute the action
			result = action_function(entities, user_preference)
			result["action_name"] = action_def.action_name
			
			return result
			
		except Exception as e:
			frappe.log_error(f"Action execution error: {str(e)}")
			return {
				"success": False,
				"error": f"Action execution failed: {str(e)}",
				"action_name": None
			}
	
	def create_sales_order(self, entities, user_preference):
		"""Create a sales order"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Sales Order", "create"):
				return {
					"success": False,
					"error": "You don't have permission to create Sales Orders"
				}
			
			# Extract entities
			customer = entities.get("customer_name")
			items = entities.get("items", [])
			
			if not customer:
				return {
					"success": False,
					"error": "Customer name is required to create a sales order"
				}
			
			# Create sales order using Frappe ORM
			sales_order = frappe.new_doc("Sales Order")
			sales_order.customer = customer
			sales_order.company = user_preference.default_company or frappe.defaults.get_user_default("Company")
			
			# Add items if provided
			if items:
				for item in items:
					sales_order.append("items", {
						"item_code": item.get("item_code"),
						"qty": item.get("quantity", 1),
						"rate": item.get("rate", 0)
					})
			
			sales_order.insert()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"Sales Order {sales_order.name} created successfully",
				"data": {
					"sales_order_id": sales_order.name,
					"customer": customer,
					"total": sales_order.grand_total
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to create sales order: {str(e)}"
			}
	
	def get_stock_levels(self, entities, user_preference):
		"""Get stock levels"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Stock Ledger Entry", "read"):
				return {
					"success": False,
					"error": "You don't have permission to view stock levels"
				}
			
			item_code = entities.get("item_code")
			warehouse = entities.get("warehouse")
			
			# Build filters
			filters = {}
			if item_code:
				filters["item_code"] = item_code
			if warehouse:
				filters["warehouse"] = warehouse
			
			# Get stock balance using Frappe ORM
			stock_data = frappe.db.sql("""
				SELECT item_code, warehouse, actual_qty, valuation_rate
				FROM `tabBin`
				WHERE actual_qty > 0
				{item_filter}
				{warehouse_filter}
				ORDER BY item_code, warehouse
				LIMIT 50
			""".format(
				item_filter=f"AND item_code = '{item_code}'" if item_code else "",
				warehouse_filter=f"AND warehouse = '{warehouse}'" if warehouse else ""
			), as_dict=True)
			
			return {
				"success": True,
				"message": f"Found {len(stock_data)} stock entries",
				"data": stock_data
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to get stock levels: {str(e)}"
			}
	
	def create_item(self, entities, user_preference):
		"""Create an item"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Item", "create"):
				return {
					"success": False,
					"error": "You don't have permission to create Items"
				}
			
			item_name = entities.get("item_name")
			item_group = entities.get("item_group", "All Item Groups")
			
			if not item_name:
				return {
					"success": False,
					"error": "Item name is required"
				}
			
			# Create item using Frappe ORM
			item = frappe.new_doc("Item")
			item.item_name = item_name
			item.item_code = item_name  # Use name as code for simplicity
			item.item_group = item_group
			item.stock_uom = "Nos"
			item.is_stock_item = 1
			
			item.insert()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"Item {item.name} created successfully",
				"data": {
					"item_code": item.name,
					"item_name": item.item_name,
					"item_group": item.item_group
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to create item: {str(e)}"
			}
	
	def get_customer_info(self, entities, user_preference):
		"""Get customer information"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Customer", "read"):
				return {
					"success": False,
					"error": "You don't have permission to view customer information"
				}
			
			customer_name = entities.get("customer_name")
			
			if customer_name:
				# Get specific customer
				customer = frappe.get_doc("Customer", customer_name)
				return {
					"success": True,
					"message": f"Customer information for {customer_name}",
					"data": {
						"customer_name": customer.customer_name,
						"customer_type": customer.customer_type,
						"territory": customer.territory,
						"customer_group": customer.customer_group
					}
				}
			else:
				# Get list of customers
				customers = frappe.get_all("Customer", 
					fields=["name", "customer_name", "customer_type", "territory"],
					limit=20
				)
				return {
					"success": True,
					"message": f"Found {len(customers)} customers",
					"data": customers
				}
				
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to get customer info: {str(e)}"
			}
	
	def create_customer(self, entities, user_preference):
		"""Create a customer"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Customer", "create"):
				return {
					"success": False,
					"error": "You don't have permission to create Customers"
				}
			
			customer_name = entities.get("customer_name")
			
			if not customer_name:
				return {
					"success": False,
					"error": "Customer name is required"
				}
			
			# Create customer using Frappe ORM
			customer = frappe.new_doc("Customer")
			customer.customer_name = customer_name
			customer.customer_type = "Individual"
			customer.territory = "All Territories"
			customer.customer_group = "All Customer Groups"
			
			customer.insert()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"Customer {customer.name} created successfully",
				"data": {
					"customer_id": customer.name,
					"customer_name": customer.customer_name
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to create customer: {str(e)}"
			}
	
	def get_sales_report(self, entities, user_preference):
		"""Get sales report"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Sales Invoice", "read"):
				return {
					"success": False,
					"error": "You don't have permission to view sales reports"
				}
			
			# Get sales data
			sales_data = frappe.db.sql("""
				SELECT 
					customer,
					SUM(grand_total) as total_sales,
					COUNT(*) as invoice_count
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
				GROUP BY customer
				ORDER BY total_sales DESC
				LIMIT 10
			""", as_dict=True)
			
			return {
				"success": True,
				"message": f"Sales report for last 30 days",
				"data": sales_data
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to get sales report: {str(e)}"
			}
	
	def create_warehouse(self, entities, user_preference):
		"""Create a warehouse"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Warehouse", "create"):
				return {
					"success": False,
					"error": "You don't have permission to create Warehouses"
				}
			
			warehouse_name = entities.get("warehouse_name")
			
			if not warehouse_name:
				return {
					"success": False,
					"error": "Warehouse name is required"
				}
			
			# Create warehouse using Frappe ORM
			warehouse = frappe.new_doc("Warehouse")
			warehouse.warehouse_name = warehouse_name
			warehouse.company = user_preference.default_company or frappe.defaults.get_user_default("Company")
			
			warehouse.insert()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"Warehouse {warehouse.name} created successfully",
				"data": {
					"warehouse_id": warehouse.name,
					"warehouse_name": warehouse.warehouse_name
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to create warehouse: {str(e)}"
			}
	
	def update_item_price(self, entities, user_preference):
		"""Update item price"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Item Price", "write"):
				return {
					"success": False,
					"error": "You don't have permission to update item prices"
				}
			
			item_code = entities.get("item_code")
			price = entities.get("price")
			
			if not item_code or not price:
				return {
					"success": False,
					"error": "Item code and price are required"
				}
			
			# Update or create item price
			existing_price = frappe.db.exists("Item Price", {
				"item_code": item_code,
				"price_list": "Standard Selling"
			})
			
			if existing_price:
				item_price = frappe.get_doc("Item Price", existing_price)
				item_price.price_list_rate = price
				item_price.save()
			else:
				item_price = frappe.new_doc("Item Price")
				item_price.item_code = item_code
				item_price.price_list = "Standard Selling"
				item_price.price_list_rate = price
				item_price.insert()
			
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"Price updated for {item_code}",
				"data": {
					"item_code": item_code,
					"new_price": price
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to update item price: {str(e)}"
			}
	
	def get_outstanding_invoices(self, entities, user_preference):
		"""Get outstanding invoices"""
		try:
			# Validate required permissions
			if not rbac_service.validate_erpnext_permission("Sales Invoice", "read"):
				return {
					"success": False,
					"error": "You don't have permission to view invoices"
				}
			
			# Get outstanding invoices
			invoices = frappe.db.sql("""
				SELECT 
					name,
					customer,
					posting_date,
					grand_total,
					outstanding_amount
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				AND outstanding_amount > 0
				ORDER BY posting_date DESC
				LIMIT 20
			""", as_dict=True)
			
			return {
				"success": True,
				"message": f"Found {len(invoices)} outstanding invoices",
				"data": invoices
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to get outstanding invoices: {str(e)}"
			}
	
	def manage_ollama_models(self, entities, user_preference):
		"""Manage Ollama models (System Manager only)"""
		try:
			# Check if user is System Manager
			if "System Manager" not in frappe.get_roles():
				return {
					"success": False,
					"error": "Only System Managers can manage Ollama models"
				}
			
			action = entities.get("action", "list")
			model_name = entities.get("model_name")
			
			if action == "list":
				# List available models
				from frappepilot.frappepilot.doctype.ollama_model.ollama_model import get_available_models
				models = get_available_models()
				return {
					"success": True,
					"message": f"Found {len(models)} models",
					"data": models
				}
			
			elif action == "download" and model_name:
				# Download a model
				model_doc = frappe.new_doc("Ollama Model")
				model_doc.model_name = model_name
				model_doc.display_name = model_name
				model_doc.status = "Available"
				model_doc.insert()
				
				result = model_doc.download_model()
				return {
					"success": True,
					"message": result["message"],
					"data": {"model_name": model_name}
				}
			
			elif action == "activate" and model_name:
				# Activate a model
				model_doc = frappe.get_doc("Ollama Model", model_name)
				result = model_doc.set_active()
				return {
					"success": True,
					"message": result["message"],
					"data": {"model_name": model_name}
				}
			
			else:
				return {
					"success": False,
					"error": "Invalid action or missing model name"
				}
				
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to manage Ollama models: {str(e)}"
			}
	
	def run_bench_command(self, entities, user_preference):
		"""Run bench command (System Manager only)"""
		try:
			# Check if user is System Manager
			if "System Manager" not in frappe.get_roles():
				return {
					"success": False,
					"error": "Only System Managers can run bench commands"
				}
			
			command = entities.get("command")
			
			if not command:
				return {
					"success": False,
					"error": "Command is required"
				}
			
			# Whitelist of allowed bench commands for security
			allowed_commands = [
				"bench version",
				"bench status",
				"bench restart",
				"bench update",
				"bench migrate",
				"bench build"
			]
			
			if command not in allowed_commands:
				return {
					"success": False,
					"error": f"Command '{command}' is not allowed. Allowed commands: {', '.join(allowed_commands)}"
				}
			
			# Execute the command safely
			try:
				result = subprocess.run(
					command.split(),
					capture_output=True,
					text=True,
					timeout=60,
					check=True
				)
				
				return {
					"success": True,
					"message": f"Command executed successfully",
					"data": {
						"command": command,
						"output": result.stdout,
						"error": result.stderr
					}
				}
				
			except subprocess.CalledProcessError as e:
				return {
					"success": False,
					"error": f"Command failed: {e.stderr}"
				}
			except subprocess.TimeoutExpired:
				return {
					"success": False,
					"error": "Command timed out"
				}
				
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to run bench command: {str(e)}"
			}
	
	def create_user(self, entities, user_preference):
		"""Create a user (System Manager only)"""
		try:
			# Check if user is System Manager
			if "System Manager" not in frappe.get_roles():
				return {
					"success": False,
					"error": "Only System Managers can create users"
				}
			
			email = entities.get("email")
			first_name = entities.get("first_name")
			last_name = entities.get("last_name")
			
			if not email or not first_name:
				return {
					"success": False,
					"error": "Email and first name are required"
				}
			
			# Create user using Frappe ORM
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = first_name
			user.last_name = last_name or ""
			user.send_welcome_email = 1
			
			user.insert()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": f"User {user.name} created successfully",
				"data": {
					"user_id": user.name,
					"email": user.email,
					"full_name": user.full_name
				}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to create user: {str(e)}"
			}
	
	def general_query(self, entities, user_preference):
		"""Handle general queries"""
		try:
			# For general queries, we just return a success message
			# The actual AI response will be generated by Ollama
			return {
				"success": True,
				"message": "General query processed",
				"data": {}
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": f"Failed to process general query: {str(e)}"
			}

# Global instance
action_executor = ActionExecutor()

