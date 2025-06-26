# Copyright (c) 2025, kbtisuu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import subprocess
import json
import threading
import time

class OllamaModel(Document):
	def validate(self):
		"""Validate the model"""
		if not self.model_name:
			frappe.throw("Model Name is required")
		
		if not self.display_name:
			self.display_name = self.model_name
	
	def before_save(self):
		"""Before save operations"""
		# If this model is being set as active, deactivate all others
		if self.is_active:
			frappe.db.sql("UPDATE `tabOllama Model` SET is_active = 0 WHERE name != %s", (self.name,))
			
			# Update the active model in settings
			settings = frappe.get_single("FrappePilot Settings")
			settings.active_model = self.model_name
			settings.save(ignore_permissions=True)
	
	def download_model(self):
		"""Download the model using ollama pull"""
		if not frappe.has_permission("Ollama Model", "write"):
			frappe.throw("Insufficient permissions to download models")
		
		# Check if user has System Manager role
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Managers can download models")
		
		self.status = "Downloading"
		self.download_progress = 0
		self.save(ignore_permissions=True)
		frappe.db.commit()
		
		# Start download in background thread
		thread = threading.Thread(target=self._download_model_background)
		thread.daemon = True
		thread.start()
		
		return {"message": f"Download started for model {self.model_name}"}
	
	def _download_model_background(self):
		"""Background thread for downloading model"""
		try:
			# Use subprocess to run ollama pull
			cmd = ["ollama", "pull", self.model_name]
			process = subprocess.Popen(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				bufsize=1,
				universal_newlines=True
			)
			
			# Monitor the process
			while True:
				output = process.stdout.readline()
				if output == '' and process.poll() is not None:
					break
				if output:
					# Try to parse progress from output
					try:
						if "pulling" in output.lower():
							# Simple progress estimation
							self.download_progress = min(self.download_progress + 10, 90)
							self.save(ignore_permissions=True)
							frappe.db.commit()
					except:
						pass
			
			# Check if process completed successfully
			return_code = process.poll()
			if return_code == 0:
				self.status = "Downloaded"
				self.download_progress = 100
				frappe.publish_realtime(
					"model_download_complete",
					{"model_name": self.model_name, "status": "success"},
					user=frappe.session.user
				)
			else:
				self.status = "Error"
				self.download_progress = 0
				error_output = process.stderr.read()
				frappe.publish_realtime(
					"model_download_complete",
					{"model_name": self.model_name, "status": "error", "error": error_output},
					user=frappe.session.user
				)
			
			self.save(ignore_permissions=True)
			frappe.db.commit()
			
		except Exception as e:
			self.status = "Error"
			self.download_progress = 0
			self.save(ignore_permissions=True)
			frappe.db.commit()
			
			frappe.publish_realtime(
				"model_download_complete",
				{"model_name": self.model_name, "status": "error", "error": str(e)},
				user=frappe.session.user
			)
	
	def remove_model(self):
		"""Remove the model using ollama rm"""
		if not frappe.has_permission("Ollama Model", "delete"):
			frappe.throw("Insufficient permissions to remove models")
		
		# Check if user has System Manager role
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Managers can remove models")
		
		try:
			# Use subprocess to run ollama rm
			cmd = ["ollama", "rm", self.model_name]
			result = subprocess.run(
				cmd,
				capture_output=True,
				text=True,
				check=True
			)
			
			# Delete the document
			self.delete()
			frappe.db.commit()
			
			return {"message": f"Model {self.model_name} removed successfully"}
			
		except subprocess.CalledProcessError as e:
			frappe.throw(f"Failed to remove model: {e.stderr}")
		except Exception as e:
			frappe.throw(f"Error removing model: {str(e)}")
	
	def set_active(self):
		"""Set this model as the active model"""
		if not frappe.has_permission("Ollama Model", "write"):
			frappe.throw("Insufficient permissions to set active model")
		
		# Check if user has System Manager role
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Managers can set active model")
		
		# Deactivate all other models
		frappe.db.sql("UPDATE `tabOllama Model` SET is_active = 0")
		
		# Activate this model
		self.is_active = 1
		self.last_used = frappe.utils.now()
		self.save(ignore_permissions=True)
		
		# Update settings
		settings = frappe.get_single("FrappePilot Settings")
		settings.active_model = self.model_name
		settings.save(ignore_permissions=True)
		
		frappe.db.commit()
		
		return {"message": f"Model {self.model_name} set as active"}

@frappe.whitelist()
def get_available_models():
	"""Get list of available models from Ollama"""
	try:
		# Use subprocess to run ollama list
		cmd = ["ollama", "list"]
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			check=True
		)
		
		models = []
		lines = result.stdout.strip().split('\n')[1:]  # Skip header
		
		for line in lines:
			if line.strip():
				parts = line.split()
				if len(parts) >= 3:
					model_name = parts[0]
					size = parts[2] if len(parts) > 2 else "Unknown"
					models.append({
						"model_name": model_name,
						"size": size
					})
		
		return models
		
	except subprocess.CalledProcessError as e:
		frappe.throw(f"Failed to get model list: {e.stderr}")
	except Exception as e:
		frappe.throw(f"Error getting model list: {str(e)}")

@frappe.whitelist()
def sync_models():
	"""Sync models from Ollama with the database"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Only System Managers can sync models")
	
	try:
		available_models = get_available_models()
		
		for model_data in available_models:
			model_name = model_data["model_name"]
			
			# Check if model already exists in database
			if not frappe.db.exists("Ollama Model", model_name):
				# Create new model document
				model_doc = frappe.new_doc("Ollama Model")
				model_doc.model_name = model_name
				model_doc.display_name = model_name
				model_doc.size = model_data["size"]
				model_doc.status = "Downloaded"
				model_doc.download_progress = 100
				model_doc.insert(ignore_permissions=True)
		
		frappe.db.commit()
		return {"message": "Models synced successfully"}
		
	except Exception as e:
		frappe.throw(f"Error syncing models: {str(e)}")

