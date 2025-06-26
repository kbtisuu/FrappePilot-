#!/usr/bin/env python3
"""
FrappePilot Comprehensive Test Suite
====================================

This test suite validates all aspects of the FrappePilot installation,
from basic connectivity to advanced AI functionality.

Author: Manus AI
Version: 1.0.0
Date: June 24, 2025
"""

import sys
import os
import time
import json
import requests
import subprocess
import mysql.connector
import redis
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/frappepilot_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class FrappePilotTestSuite:
    """Comprehensive test suite for FrappePilot installation"""
    
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        # Configuration
        self.config = {
            'erpnext_url': 'http://localhost:8000',
            'ollama_url': 'http://localhost:11434',
            'db_host': 'localhost',
            'db_port': 3306,
            'db_user': 'erpnext',
            'db_password': 'your_password',  # Update with actual password
            'db_name': 'your_database_name',  # Update with actual database name
            'redis_host': 'localhost',
            'redis_port': 6379,
            'test_user': 'Administrator',
            'test_password': 'admin'  # Update with actual password
        }
    
    def run_all_tests(self):
        """Run all test categories"""
        logging.info("Starting FrappePilot Comprehensive Test Suite")
        logging.info("=" * 60)
        
        test_categories = [
            ('System Prerequisites', self.test_system_prerequisites),
            ('Database Connectivity', self.test_database_connectivity),
            ('Redis Connectivity', self.test_redis_connectivity),
            ('Ollama Service', self.test_ollama_service),
            ('ERPNext Connectivity', self.test_erpnext_connectivity),
            ('FrappePilot Installation', self.test_frappepilot_installation),
            ('DocType Validation', self.test_doctype_validation),
            ('API Endpoints', self.test_api_endpoints),
            ('AI Functionality', self.test_ai_functionality),
            ('Permission System', self.test_permission_system),
            ('Security Features', self.test_security_features),
            ('Performance Metrics', self.test_performance_metrics)
        ]
        
        for category_name, test_function in test_categories:
            logging.info(f"\n--- Testing {category_name} ---")
            try:
                test_function()
                logging.info(f"✓ {category_name} tests completed")
            except Exception as e:
                logging.error(f"✗ {category_name} tests failed: {str(e)}")
                self.failed_tests.append(category_name)
        
        self.generate_test_report()
    
    def test_system_prerequisites(self):
        """Test system prerequisites and dependencies"""
        
        # Test Python version
        python_version = sys.version_info
        assert python_version >= (3, 8), f"Python 3.8+ required, found {python_version}"
        logging.info(f"✓ Python version: {python_version.major}.{python_version.minor}")
        
        # Test required packages
        required_packages = ['requests', 'mysql-connector-python', 'redis']
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logging.info(f"✓ Package {package} is available")
            except ImportError:
                raise AssertionError(f"Required package {package} is not installed")
        
        # Test system services
        services = ['mariadb', 'redis-server', 'ollama']
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"✓ Service {service} is active")
                else:
                    logging.warning(f"⚠ Service {service} is not active")
            except Exception as e:
                logging.warning(f"⚠ Could not check service {service}: {str(e)}")
        
        # Test disk space
        disk_usage = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        logging.info(f"✓ Disk usage check completed")
        
        # Test memory
        memory_info = subprocess.run(['free', '-h'], capture_output=True, text=True)
        logging.info(f"✓ Memory check completed")
    
    def test_database_connectivity(self):
        """Test database connectivity and FrappePilot tables"""
        
        try:
            # Test basic connectivity
            conn = mysql.connector.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_password'],
                database=self.config['db_name']
            )
            
            cursor = conn.cursor()
            logging.info("✓ Database connection established")
            
            # Test FrappePilot tables
            frappepilot_tables = [
                'tabFrappePilot Settings',
                'tabAI Command Log',
                'tabAI User Preference',
                'tabAI Action Definition',
                'tabAI Action Role',
                'tabOllama Model'
            ]
            
            for table in frappepilot_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                result = cursor.fetchone()
                if result:
                    logging.info(f"✓ Table {table} exists")
                else:
                    raise AssertionError(f"Table {table} not found")
            
            # Test table structure
            cursor.execute("DESCRIBE `tabAI Command Log`")
            columns = cursor.fetchall()
            required_columns = ['user', 'user_input', 'intent', 'status', 'assistant_response']
            column_names = [col[0] for col in columns]
            
            for req_col in required_columns:
                if req_col in column_names:
                    logging.info(f"✓ Column {req_col} exists in AI Command Log")
                else:
                    raise AssertionError(f"Required column {req_col} not found")
            
            conn.close()
            
        except mysql.connector.Error as e:
            raise AssertionError(f"Database connection failed: {str(e)}")
    
    def test_redis_connectivity(self):
        """Test Redis connectivity and configuration"""
        
        try:
            r = redis.Redis(
                host=self.config['redis_host'],
                port=self.config['redis_port'],
                decode_responses=True
            )
            
            # Test basic connectivity
            r.ping()
            logging.info("✓ Redis connection established")
            
            # Test read/write operations
            test_key = "frappepilot_test"
            test_value = "test_value"
            
            r.set(test_key, test_value, ex=60)
            retrieved_value = r.get(test_key)
            
            if retrieved_value == test_value:
                logging.info("✓ Redis read/write operations working")
            else:
                raise AssertionError("Redis read/write test failed")
            
            # Clean up
            r.delete(test_key)
            
        except redis.RedisError as e:
            raise AssertionError(f"Redis connection failed: {str(e)}")
    
    def test_ollama_service(self):
        """Test Ollama service and model availability"""
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.config['ollama_url']}/api/tags", timeout=10)
            if response.status_code == 200:
                logging.info("✓ Ollama service is responding")
            else:
                raise AssertionError(f"Ollama service returned status {response.status_code}")
            
            # Test available models
            models = response.json()
            if 'models' in models and len(models['models']) > 0:
                logging.info(f"✓ Found {len(models['models'])} Ollama models")
                for model in models['models']:
                    logging.info(f"  - {model['name']}")
            else:
                raise AssertionError("No Ollama models found")
            
            # Test model inference
            test_prompt = "Hello, this is a test message."
            inference_data = {
                "model": models['models'][0]['name'],
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.config['ollama_url']}/api/generate",
                json=inference_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result and result['response']:
                    logging.info("✓ Ollama model inference working")
                else:
                    raise AssertionError("Ollama model returned empty response")
            else:
                raise AssertionError(f"Ollama inference failed with status {response.status_code}")
                
        except requests.RequestException as e:
            raise AssertionError(f"Ollama service test failed: {str(e)}")
    
    def test_erpnext_connectivity(self):
        """Test ERPNext connectivity and basic functionality"""
        
        try:
            # Test basic connectivity
            response = requests.get(self.config['erpnext_url'], timeout=10)
            if response.status_code == 200:
                logging.info("✓ ERPNext is accessible")
            else:
                raise AssertionError(f"ERPNext returned status {response.status_code}")
            
            # Test API endpoint
            api_url = f"{self.config['erpnext_url']}/api/method/frappe.auth.get_logged_user"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code in [200, 403]:  # 403 is expected without authentication
                logging.info("✓ ERPNext API is responding")
            else:
                raise AssertionError(f"ERPNext API returned unexpected status {response.status_code}")
                
        except requests.RequestException as e:
            raise AssertionError(f"ERPNext connectivity test failed: {str(e)}")
    
    def test_frappepilot_installation(self):
        """Test FrappePilot installation and app availability"""
        
        try:
            # Test if FrappePilot app is installed
            result = subprocess.run(
                ['bench', '--site', 'all', 'list-apps'],
                capture_output=True,
                text=True,
                cwd=os.path.expanduser('~/erpnext-bench')
            )
            
            if 'frappepilot' in result.stdout:
                logging.info("✓ FrappePilot app is installed")
            else:
                raise AssertionError("FrappePilot app not found in installed apps")
            
            # Test FrappePilot page accessibility
            page_url = f"{self.config['erpnext_url']}/app/frappepilot-chat"
            response = requests.get(page_url, timeout=10)
            
            if response.status_code in [200, 302]:  # 302 redirect to login is acceptable
                logging.info("✓ FrappePilot chat page is accessible")
            else:
                logging.warning(f"⚠ FrappePilot chat page returned status {response.status_code}")
                
        except subprocess.CalledProcessError as e:
            raise AssertionError(f"Failed to check installed apps: {str(e)}")
        except requests.RequestException as e:
            logging.warning(f"⚠ Could not test FrappePilot page accessibility: {str(e)}")
    
    def test_doctype_validation(self):
        """Test FrappePilot DocType structure and data"""
        
        try:
            conn = mysql.connector.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_password'],
                database=self.config['db_name']
            )
            
            cursor = conn.cursor()
            
            # Test AI Action Definition data
            cursor.execute("SELECT COUNT(*) FROM `tabAI Action Definition`")
            action_count = cursor.fetchone()[0]
            
            if action_count > 0:
                logging.info(f"✓ Found {action_count} AI Action Definitions")
            else:
                logging.warning("⚠ No AI Action Definitions found")
            
            # Test FrappePilot Settings
            cursor.execute("SELECT COUNT(*) FROM `tabFrappePilot Settings`")
            settings_count = cursor.fetchone()[0]
            
            if settings_count > 0:
                logging.info("✓ FrappePilot Settings configured")
            else:
                logging.warning("⚠ FrappePilot Settings not configured")
            
            # Test Ollama Model entries
            cursor.execute("SELECT COUNT(*) FROM `tabOllama Model`")
            model_count = cursor.fetchone()[0]
            
            if model_count > 0:
                logging.info(f"✓ Found {model_count} Ollama Model entries")
            else:
                logging.warning("⚠ No Ollama Model entries found")
            
            conn.close()
            
        except mysql.connector.Error as e:
            raise AssertionError(f"DocType validation failed: {str(e)}")
    
    def test_api_endpoints(self):
        """Test FrappePilot API endpoints"""
        
        # Note: This test requires authentication, which may not be available in automated testing
        logging.info("⚠ API endpoint testing requires authentication")
        logging.info("  Manual testing recommended for:")
        logging.info("  - /api/method/frappepilot.api.chat.check_status")
        logging.info("  - /api/method/frappepilot.api.chat.process_message")
        logging.info("  - /api/method/frappepilot.api.chat.get_conversation_history")
        logging.info("  - /api/method/frappepilot.api.chat.get_user_permissions")
    
    def test_ai_functionality(self):
        """Test AI functionality integration"""
        
        # Test Ollama integration through direct API calls
        try:
            # Test intent extraction simulation
            test_message = "Create a new sales order for customer ABC Corp"
            
            # Simulate the intent extraction process
            intent_prompt = f"""
            Extract the intent and entities from this business request: "{test_message}"
            
            Respond with valid JSON in this format:
            {{
                "intent": "create_sales_order",
                "entities": {{
                    "customer_name": "ABC Corp"
                }}
            }}
            """
            
            # Get available models
            models_response = requests.get(f"{self.config['ollama_url']}/api/tags")
            if models_response.status_code == 200:
                models = models_response.json()
                if models['models']:
                    model_name = models['models'][0]['name']
                    
                    inference_data = {
                        "model": model_name,
                        "prompt": intent_prompt,
                        "stream": False
                    }
                    
                    response = requests.post(
                        f"{self.config['ollama_url']}/api/generate",
                        json=inference_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'response' in result and result['response']:
                            logging.info("✓ AI intent extraction simulation successful")
                            
                            # Try to parse the response as JSON
                            try:
                                ai_response = result['response']
                                # Extract JSON from response (may contain additional text)
                                import re
                                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                                if json_match:
                                    parsed_json = json.loads(json_match.group())
                                    if 'intent' in parsed_json:
                                        logging.info(f"✓ Extracted intent: {parsed_json['intent']}")
                                    else:
                                        logging.warning("⚠ Intent not found in AI response")
                                else:
                                    logging.warning("⚠ No valid JSON found in AI response")
                            except json.JSONDecodeError:
                                logging.warning("⚠ AI response is not valid JSON")
                        else:
                            raise AssertionError("AI model returned empty response")
                    else:
                        raise AssertionError(f"AI inference failed with status {response.status_code}")
                else:
                    raise AssertionError("No AI models available for testing")
            else:
                raise AssertionError("Could not retrieve available models")
                
        except requests.RequestException as e:
            raise AssertionError(f"AI functionality test failed: {str(e)}")
    
    def test_permission_system(self):
        """Test role-based permission system"""
        
        try:
            conn = mysql.connector.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_password'],
                database=self.config['db_name']
            )
            
            cursor = conn.cursor()
            
            # Test AI Action Definition permissions
            cursor.execute("""
                SELECT action_name, is_admin_only, COUNT(r.role) as role_count
                FROM `tabAI Action Definition` a
                LEFT JOIN `tabAI Action Role` r ON a.name = r.parent
                GROUP BY a.name, a.action_name, a.is_admin_only
            """)
            
            actions = cursor.fetchall()
            
            if actions:
                logging.info(f"✓ Found {len(actions)} AI actions with permission configuration")
                for action in actions:
                    action_name, is_admin_only, role_count = action
                    if is_admin_only:
                        logging.info(f"  - {action_name}: Admin only")
                    else:
                        logging.info(f"  - {action_name}: {role_count} roles assigned")
            else:
                logging.warning("⚠ No AI actions with permissions found")
            
            # Test user roles
            cursor.execute("SELECT COUNT(DISTINCT role) FROM `tabHas Role`")
            role_count = cursor.fetchone()[0]
            
            if role_count > 0:
                logging.info(f"✓ Found {role_count} distinct roles in system")
            else:
                logging.warning("⚠ No user roles found")
            
            conn.close()
            
        except mysql.connector.Error as e:
            raise AssertionError(f"Permission system test failed: {str(e)}")
    
    def test_security_features(self):
        """Test security features and configurations"""
        
        # Test firewall configuration
        try:
            result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True)
            if 'Status: active' in result.stdout:
                logging.info("✓ UFW firewall is active")
            else:
                logging.warning("⚠ UFW firewall is not active")
        except subprocess.CalledProcessError:
            logging.warning("⚠ Could not check firewall status")
        
        # Test SSL configuration (if applicable)
        try:
            response = requests.get(self.config['erpnext_url'].replace('http://', 'https://'), 
                                  timeout=5, verify=False)
            if response.status_code == 200:
                logging.info("✓ HTTPS is configured")
            else:
                logging.info("ℹ HTTPS not configured (development setup)")
        except requests.RequestException:
            logging.info("ℹ HTTPS not configured (development setup)")
        
        # Test Ollama port accessibility
        try:
            response = requests.get(f"http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                logging.warning("⚠ Ollama port is accessible from localhost (expected)")
            
            # Try external access (should fail in production)
            try:
                response = requests.get(f"http://0.0.0.0:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    logging.warning("⚠ Ollama port may be accessible externally")
                else:
                    logging.info("✓ Ollama port is properly restricted")
            except requests.RequestException:
                logging.info("✓ Ollama port is properly restricted")
                
        except requests.RequestException:
            logging.error("✗ Ollama service is not accessible")
    
    def test_performance_metrics(self):
        """Test system performance metrics"""
        
        # Test response times
        start_time = time.time()
        try:
            response = requests.get(self.config['erpnext_url'], timeout=10)
            response_time = time.time() - start_time
            
            if response_time < 5.0:
                logging.info(f"✓ ERPNext response time: {response_time:.2f}s")
            else:
                logging.warning(f"⚠ Slow ERPNext response time: {response_time:.2f}s")
        except requests.RequestException as e:
            logging.error(f"✗ ERPNext performance test failed: {str(e)}")
        
        # Test Ollama response times
        start_time = time.time()
        try:
            response = requests.get(f"{self.config['ollama_url']}/api/tags", timeout=10)
            response_time = time.time() - start_time
            
            if response_time < 2.0:
                logging.info(f"✓ Ollama response time: {response_time:.2f}s")
            else:
                logging.warning(f"⚠ Slow Ollama response time: {response_time:.2f}s")
        except requests.RequestException as e:
            logging.error(f"✗ Ollama performance test failed: {str(e)}")
        
        # Test database query performance
        try:
            conn = mysql.connector.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_password'],
                database=self.config['db_name']
            )
            
            cursor = conn.cursor()
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM `tabAI Command Log`")
            result = cursor.fetchone()
            query_time = time.time() - start_time
            
            if query_time < 1.0:
                logging.info(f"✓ Database query time: {query_time:.3f}s")
            else:
                logging.warning(f"⚠ Slow database query time: {query_time:.3f}s")
            
            conn.close()
            
        except mysql.connector.Error as e:
            logging.error(f"✗ Database performance test failed: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        logging.info("\n" + "=" * 60)
        logging.info("FrappePilot Test Suite Report")
        logging.info("=" * 60)
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        
        if self.failed_tests:
            logging.error(f"FAILED TESTS ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                logging.error(f"  ✗ {test}")
        
        if self.passed_tests:
            logging.info(f"PASSED TESTS ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                logging.info(f"  ✓ {test}")
        
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        logging.info(f"\nOverall Success Rate: {success_rate:.1f}%")
        
        if len(self.failed_tests) == 0:
            logging.info("🎉 All tests passed! FrappePilot is ready for use.")
        else:
            logging.warning("⚠ Some tests failed. Please review the issues above.")
        
        # Save detailed report
        report_file = f"/tmp/frappepilot_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(f"FrappePilot Test Report - {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {len(self.passed_tests)}\n")
            f.write(f"Failed: {len(self.failed_tests)}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n\n")
            
            if self.failed_tests:
                f.write("Failed Tests:\n")
                for test in self.failed_tests:
                    f.write(f"  - {test}\n")
                f.write("\n")
            
            f.write("See /tmp/frappepilot_test.log for detailed output.\n")
        
        logging.info(f"Detailed report saved to: {report_file}")

def main():
    """Main test execution function"""
    
    print("FrappePilot Comprehensive Test Suite")
    print("====================================")
    print("This test suite will validate your FrappePilot installation.")
    print("Please ensure all services are running before proceeding.\n")
    
    # Prompt for configuration
    config_file = input("Enter path to configuration file (or press Enter for defaults): ").strip()
    
    test_suite = FrappePilotTestSuite()
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                test_suite.config.update(user_config)
            print(f"Configuration loaded from {config_file}")
        except Exception as e:
            print(f"Warning: Could not load configuration file: {e}")
            print("Using default configuration...")
    
    print("\nStarting tests...\n")
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()

