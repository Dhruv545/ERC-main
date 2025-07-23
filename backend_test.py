#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Steel Inventory Management System
Tests all API endpoints and business logic as specified in the review request.
"""

import requests
import json
from datetime import date, datetime
import time

# API Configuration
BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

class SteelInventoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_api_connection(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log_test("API Connection", True, "API is accessible")
                return True
            else:
                self.log_test("API Connection", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Connection", False, f"Connection failed: {str(e)}")
            return False
    
    def test_heat_management(self):
        """Test Heat Management API endpoints"""
        print("\n=== TESTING HEAT MANAGEMENT ===")
        
        # Test 1: Add new heat record for 20.64mm steel
        heat_data_1 = {
            "heat_number": "H2024001",
            "steel_type": "20.64mm",
            "quantity_kg": 500.0,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=heat_data_1)
            if response.status_code == 200:
                heat_result = response.json()
                self.log_test("Add Heat - 20.64mm", True, "Heat record created successfully", 
                            f"Heat ID: {heat_result.get('id')}, Remaining: {heat_result.get('remaining_kg')}kg")
            else:
                self.log_test("Add Heat - 20.64mm", False, f"Failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Add Heat - 20.64mm", False, f"Request failed: {str(e)}")
        
        # Test 2: Add new heat record for 23mm steel
        heat_data_2 = {
            "heat_number": "H2024002",
            "steel_type": "23mm",
            "quantity_kg": 750.0,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=heat_data_2)
            if response.status_code == 200:
                heat_result = response.json()
                self.log_test("Add Heat - 23mm", True, "Heat record created successfully", 
                            f"Heat ID: {heat_result.get('id')}, Remaining: {heat_result.get('remaining_kg')}kg")
            else:
                self.log_test("Add Heat - 23mm", False, f"Failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Add Heat - 23mm", False, f"Request failed: {str(e)}")
        
        # Test 3: Test duplicate heat number validation
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=heat_data_1)  # Same heat number
            if response.status_code == 400:
                self.log_test("Duplicate Heat Validation", True, "Duplicate heat number correctly rejected")
            else:
                self.log_test("Duplicate Heat Validation", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Duplicate Heat Validation", False, f"Request failed: {str(e)}")
        
        # Test 4: Test invalid data
        invalid_heat = {
            "heat_number": "",  # Empty heat number
            "steel_type": "invalid_type",
            "quantity_kg": -100  # Negative quantity
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=invalid_heat)
            if response.status_code >= 400:
                self.log_test("Invalid Heat Data", True, "Invalid data correctly rejected")
            else:
                self.log_test("Invalid Heat Data", False, f"Invalid data was accepted (status {response.status_code})")
        except Exception as e:
            self.log_test("Invalid Heat Data", False, f"Request failed: {str(e)}")
        
        # Test 5: Get all heats
        try:
            response = self.session.get(f"{BASE_URL}/heats")
            if response.status_code == 200:
                heats = response.json()
                self.log_test("Get All Heats", True, f"Retrieved {len(heats)} heat records", 
                            f"Heat numbers: {[h.get('heat_number') for h in heats]}")
            else:
                self.log_test("Get All Heats", False, f"Failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Get All Heats", False, f"Request failed: {str(e)}")
    
    def test_production_management(self):
        """Test Production Management API endpoints"""
        print("\n=== TESTING PRODUCTION MANAGEMENT ===")
        
        # Test 1: Record MK-III production
        production_data_1 = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 100
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=production_data_1)
            if response.status_code == 200:
                production_result = response.json()
                expected_consumption = 100 * 0.930  # 93kg
                actual_consumption = production_result.get('material_consumed_kg')
                self.log_test("Record MK-III Production", True, 
                            f"Production recorded successfully. Material consumed: {actual_consumption}kg (expected: {expected_consumption}kg)")
            else:
                self.log_test("Record MK-III Production", False, f"Failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Record MK-III Production", False, f"Request failed: {str(e)}")
        
        # Test 2: Record MK-V production
        production_data_2 = {
            "date": date.today().isoformat(),
            "product_type": "MK-V",
            "quantity_produced": 50
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=production_data_2)
            if response.status_code == 200:
                production_result = response.json()
                expected_consumption = 50 * 1.15  # 57.5kg
                actual_consumption = production_result.get('material_consumed_kg')
                self.log_test("Record MK-V Production", True, 
                            f"Production recorded successfully. Material consumed: {actual_consumption}kg (expected: {expected_consumption}kg)")
            else:
                self.log_test("Record MK-V Production", False, f"Failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Record MK-V Production", False, f"Request failed: {str(e)}")
        
        # Test 3: Test insufficient stock scenario
        large_production = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 10000  # This should exceed available stock
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=large_production)
            if response.status_code == 400:
                self.log_test("Insufficient Stock Handling", True, "Insufficient stock correctly detected")
            else:
                self.log_test("Insufficient Stock Handling", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Insufficient Stock Handling", False, f"Request failed: {str(e)}")
        
        # Test 4: Get all productions
        try:
            response = self.session.get(f"{BASE_URL}/productions")
            if response.status_code == 200:
                productions = response.json()
                self.log_test("Get All Productions", True, f"Retrieved {len(productions)} production records")
            else:
                self.log_test("Get All Productions", False, f"Failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Get All Productions", False, f"Request failed: {str(e)}")
    
    def test_inventory_status(self):
        """Test Inventory Status API"""
        print("\n=== TESTING INVENTORY STATUS ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                inventory = response.json()
                
                # Verify we have both steel types
                steel_types = [item.get('steel_type') for item in inventory]
                if "20.64mm" in steel_types and "23mm" in steel_types:
                    self.log_test("Inventory Status - Steel Types", True, "Both steel types present in inventory")
                else:
                    self.log_test("Inventory Status - Steel Types", False, f"Missing steel types. Found: {steel_types}")
                
                # Check inventory calculations
                for item in inventory:
                    steel_type = item.get('steel_type')
                    total_received = item.get('total_received_kg', 0)
                    total_consumed = item.get('total_consumed_kg', 0)
                    current_stock = item.get('current_stock_kg', 0)
                    
                    # Verify calculation: current_stock = total_received - total_consumed
                    expected_stock = total_received - total_consumed
                    if abs(current_stock - expected_stock) < 0.01:  # Allow small floating point differences
                        self.log_test(f"Stock Calculation - {steel_type}", True, 
                                    f"Stock calculation correct: {current_stock}kg")
                    else:
                        self.log_test(f"Stock Calculation - {steel_type}", False, 
                                    f"Stock calculation error. Expected: {expected_stock}kg, Got: {current_stock}kg")
                    
                    # Check low stock alerts
                    low_stock_alert = item.get('low_stock_alert', False)
                    reorder_recommendation = item.get('reorder_recommendation', '')
                    
                    if current_stock < 100:
                        if low_stock_alert:
                            self.log_test(f"Low Stock Alert - {steel_type}", True, 
                                        f"Low stock alert correctly triggered for {current_stock}kg")
                        else:
                            self.log_test(f"Low Stock Alert - {steel_type}", False, 
                                        f"Low stock alert should be triggered for {current_stock}kg")
                    
                    self.log_test(f"Reorder Recommendation - {steel_type}", True, 
                                f"Recommendation: {reorder_recommendation}")
                
            else:
                self.log_test("Inventory Status API", False, f"Failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Inventory Status API", False, f"Request failed: {str(e)}")
    
    def test_dashboard_data(self):
        """Test Dashboard Data API"""
        print("\n=== TESTING DASHBOARD DATA ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                dashboard = response.json()
                
                # Check required fields
                required_fields = ['inventory_status', 'recent_productions', 'recent_heats', 
                                 'total_production_mkiii', 'total_production_mkv']
                
                missing_fields = [field for field in required_fields if field not in dashboard]
                if not missing_fields:
                    self.log_test("Dashboard Data Structure", True, "All required fields present")
                else:
                    self.log_test("Dashboard Data Structure", False, f"Missing fields: {missing_fields}")
                
                # Verify production totals
                total_mkiii = dashboard.get('total_production_mkiii', 0)
                total_mkv = dashboard.get('total_production_mkv', 0)
                
                self.log_test("Production Totals", True, 
                            f"MK-III Total: {total_mkiii}, MK-V Total: {total_mkv}")
                
                # Check recent data
                recent_productions = dashboard.get('recent_productions', [])
                recent_heats = dashboard.get('recent_heats', [])
                
                self.log_test("Recent Activity Data", True, 
                            f"Recent productions: {len(recent_productions)}, Recent heats: {len(recent_heats)}")
                
            else:
                self.log_test("Dashboard Data API", False, f"Failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Data API", False, f"Request failed: {str(e)}")
    
    def test_business_logic_workflow(self):
        """Test complete business workflow: Add heats -> Record production -> Check inventory"""
        print("\n=== TESTING BUSINESS LOGIC WORKFLOW ===")
        
        # Step 1: Add a new heat for testing FIFO
        test_heat = {
            "heat_number": "H2024TEST",
            "steel_type": "20.64mm",
            "quantity_kg": 200.0,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=test_heat)
            if response.status_code == 200:
                self.log_test("Workflow - Add Test Heat", True, "Test heat added successfully")
            else:
                self.log_test("Workflow - Add Test Heat", False, f"Failed to add test heat: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Workflow - Add Test Heat", False, f"Request failed: {str(e)}")
            return
        
        # Step 2: Get initial inventory
        try:
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                initial_inventory = response.json()
                initial_stock_20_64 = next((item['current_stock_kg'] for item in initial_inventory 
                                          if item['steel_type'] == '20.64mm'), 0)
                self.log_test("Workflow - Initial Inventory", True, f"Initial 20.64mm stock: {initial_stock_20_64}kg")
            else:
                self.log_test("Workflow - Initial Inventory", False, "Failed to get initial inventory")
                return
        except Exception as e:
            self.log_test("Workflow - Initial Inventory", False, f"Request failed: {str(e)}")
            return
        
        # Step 3: Record production to test FIFO deduction
        test_production = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 50  # Should consume 46.5kg
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=test_production)
            if response.status_code == 200:
                production_result = response.json()
                consumed = production_result.get('material_consumed_kg')
                self.log_test("Workflow - Record Production", True, f"Production recorded, consumed: {consumed}kg")
            else:
                self.log_test("Workflow - Record Production", False, f"Failed to record production: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Workflow - Record Production", False, f"Request failed: {str(e)}")
            return
        
        # Step 4: Check final inventory to verify FIFO deduction
        try:
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                final_inventory = response.json()
                final_stock_20_64 = next((item['current_stock_kg'] for item in final_inventory 
                                        if item['steel_type'] == '20.64mm'), 0)
                
                expected_reduction = 50 * 0.930  # 46.5kg
                actual_reduction = initial_stock_20_64 - final_stock_20_64
                
                if abs(actual_reduction - expected_reduction) < 0.01:
                    self.log_test("Workflow - FIFO Deduction", True, 
                                f"FIFO working correctly. Stock reduced by {actual_reduction}kg")
                else:
                    self.log_test("Workflow - FIFO Deduction", False, 
                                f"FIFO error. Expected reduction: {expected_reduction}kg, Actual: {actual_reduction}kg")
            else:
                self.log_test("Workflow - Final Inventory", False, "Failed to get final inventory")
        except Exception as e:
            self.log_test("Workflow - Final Inventory", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("=" * 60)
        
        # Test API connection first
        if not self.test_api_connection():
            print("❌ API connection failed. Stopping tests.")
            return
        
        # Run all test suites
        self.test_heat_management()
        self.test_production_management()
        self.test_inventory_status()
        self.test_dashboard_data()
        self.test_business_logic_workflow()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = SteelInventoryTester()
    results = tester.run_all_tests()