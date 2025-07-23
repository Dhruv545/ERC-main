#!/usr/bin/env python3
"""
Comprehensive Testing for Heat Editing and Deletion Functionality
Tests the new PUT /api/heat/{heat_id} and DELETE /api/heat/{heat_id} endpoints
"""

import requests
import json
from datetime import date, datetime
import time

# API Configuration
BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

class HeatEditDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_heat_ids = []  # Store heat IDs for cleanup
        
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
    
    def setup_test_data(self):
        """Create test heat records for testing"""
        print("\n=== SETTING UP TEST DATA ===")
        
        # Create multiple test heats
        test_heats = [
            {
                "heat_number": "EDIT_TEST_001",
                "steel_type": "20.64mm",
                "quantity_kg": 1000.0,
                "date_received": date.today().isoformat()
            },
            {
                "heat_number": "EDIT_TEST_002", 
                "steel_type": "23mm",
                "quantity_kg": 800.0,
                "date_received": date.today().isoformat()
            },
            {
                "heat_number": "DELETE_TEST_001",
                "steel_type": "20.64mm", 
                "quantity_kg": 500.0,
                "date_received": date.today().isoformat()
            },
            {
                "heat_number": "CONSUME_TEST_001",
                "steel_type": "20.64mm",
                "quantity_kg": 300.0,
                "date_received": date.today().isoformat()
            }
        ]
        
        for heat_data in test_heats:
            try:
                response = self.session.post(f"{BASE_URL}/heat", json=heat_data)
                if response.status_code == 200:
                    heat_result = response.json()
                    heat_id = heat_result.get('id')
                    self.test_heat_ids.append(heat_id)
                    self.log_test(f"Setup Heat {heat_data['heat_number']}", True, 
                                f"Created heat with ID: {heat_id}")
                else:
                    self.log_test(f"Setup Heat {heat_data['heat_number']}", False, 
                                f"Failed with status {response.status_code}")
            except Exception as e:
                self.log_test(f"Setup Heat {heat_data['heat_number']}", False, f"Request failed: {str(e)}")
    
    def test_heat_update_basic(self):
        """Test basic heat update functionality"""
        print("\n=== TESTING HEAT UPDATE - BASIC FUNCTIONALITY ===")
        
        if len(self.test_heat_ids) < 2:
            self.log_test("Heat Update Basic", False, "Insufficient test data")
            return
        
        heat_id = self.test_heat_ids[0]
        
        # Test 1: Update heat number, steel type, and quantity
        update_data = {
            "heat_number": "EDIT_TEST_001_UPDATED",
            "steel_type": "23mm",  # Changed from 20.64mm
            "quantity_kg": 1200.0,  # Increased quantity
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/heat/{heat_id}", json=update_data)
            if response.status_code == 200:
                updated_heat = response.json()
                self.log_test("Update Heat - Basic", True, 
                            f"Heat updated successfully. New quantity: {updated_heat.get('quantity_kg')}kg, "
                            f"Remaining: {updated_heat.get('remaining_kg')}kg")
            else:
                self.log_test("Update Heat - Basic", False, 
                            f"Failed with status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Update Heat - Basic", False, f"Request failed: {str(e)}")
    
    def test_heat_update_duplicate_number(self):
        """Test updating heat number to existing one (should fail)"""
        print("\n=== TESTING HEAT UPDATE - DUPLICATE NUMBER ===")
        
        if len(self.test_heat_ids) < 2:
            self.log_test("Heat Update Duplicate", False, "Insufficient test data")
            return
        
        heat_id = self.test_heat_ids[1]
        
        # Try to update to an existing heat number
        update_data = {
            "heat_number": "EDIT_TEST_001_UPDATED",  # This should already exist from previous test
            "steel_type": "23mm",
            "quantity_kg": 900.0
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/heat/{heat_id}", json=update_data)
            if response.status_code == 400:
                self.log_test("Update Heat - Duplicate Number", True, 
                            "Duplicate heat number correctly rejected")
            else:
                self.log_test("Update Heat - Duplicate Number", False, 
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Update Heat - Duplicate Number", False, f"Request failed: {str(e)}")
    
    def test_heat_update_with_consumption(self):
        """Test updating quantity when material has been consumed"""
        print("\n=== TESTING HEAT UPDATE - WITH CONSUMPTION ===")
        
        if len(self.test_heat_ids) < 4:
            self.log_test("Heat Update With Consumption", False, "Insufficient test data")
            return
        
        heat_id = self.test_heat_ids[3]  # CONSUME_TEST_001
        
        # First, consume some material from this heat by recording production
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 100  # Should consume 93kg (100 * 0.930)
        }
        
        try:
            # Record production to consume material
            response = self.session.post(f"{BASE_URL}/production", json=production_data)
            if response.status_code == 200:
                self.log_test("Setup - Record Production", True, "Production recorded to consume material")
                
                # Now try to update the heat quantity below consumed amount
                update_data = {
                    "heat_number": "CONSUME_TEST_001_UPDATED",
                    "steel_type": "20.64mm",
                    "quantity_kg": 50.0  # Less than consumed (93kg)
                }
                
                response = self.session.put(f"{BASE_URL}/heat/{heat_id}", json=update_data)
                if response.status_code == 400:
                    self.log_test("Update Heat - Below Consumed", True, 
                                "Update correctly rejected when quantity below consumed amount")
                else:
                    self.log_test("Update Heat - Below Consumed", False, 
                                f"Expected 400, got {response.status_code}")
                
                # Test valid update (quantity above consumed amount)
                update_data["quantity_kg"] = 150.0  # Above consumed amount
                response = self.session.put(f"{BASE_URL}/heat/{heat_id}", json=update_data)
                if response.status_code == 200:
                    updated_heat = response.json()
                    remaining = updated_heat.get('remaining_kg')
                    expected_remaining = 150.0 - 93.0  # 57kg
                    if abs(remaining - expected_remaining) < 0.1:
                        self.log_test("Update Heat - Above Consumed", True, 
                                    f"Heat updated correctly. Remaining: {remaining}kg (expected: {expected_remaining}kg)")
                    else:
                        self.log_test("Update Heat - Above Consumed", False, 
                                    f"Remaining quantity incorrect. Got: {remaining}kg, Expected: {expected_remaining}kg")
                else:
                    self.log_test("Update Heat - Above Consumed", False, 
                                f"Valid update failed with status {response.status_code}")
            else:
                self.log_test("Setup - Record Production", False, 
                            f"Failed to record production: {response.status_code}")
        except Exception as e:
            self.log_test("Heat Update With Consumption", False, f"Request failed: {str(e)}")
    
    def test_heat_update_edge_cases(self):
        """Test edge cases for heat updates"""
        print("\n=== TESTING HEAT UPDATE - EDGE CASES ===")
        
        # Test 1: Update non-existent heat
        fake_heat_id = "non-existent-id"
        update_data = {
            "heat_number": "FAKE_HEAT",
            "steel_type": "20.64mm",
            "quantity_kg": 100.0
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/heat/{fake_heat_id}", json=update_data)
            if response.status_code == 404:
                self.log_test("Update Non-existent Heat", True, "Non-existent heat correctly rejected")
            else:
                self.log_test("Update Non-existent Heat", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Update Non-existent Heat", False, f"Request failed: {str(e)}")
        
        # Test 2: Update with invalid data
        if self.test_heat_ids:
            heat_id = self.test_heat_ids[0]
            invalid_data = {
                "heat_number": "",  # Empty heat number
                "steel_type": "invalid_type",
                "quantity_kg": -100  # Negative quantity
            }
            
            try:
                response = self.session.put(f"{BASE_URL}/heat/{heat_id}", json=invalid_data)
                if response.status_code >= 400:
                    self.log_test("Update Invalid Data", True, "Invalid data correctly rejected")
                else:
                    self.log_test("Update Invalid Data", False, f"Invalid data accepted: {response.status_code}")
            except Exception as e:
                self.log_test("Update Invalid Data", False, f"Request failed: {str(e)}")
    
    def test_heat_deletion_basic(self):
        """Test basic heat deletion functionality"""
        print("\n=== TESTING HEAT DELETION - BASIC FUNCTIONALITY ===")
        
        if len(self.test_heat_ids) < 3:
            self.log_test("Heat Deletion Basic", False, "Insufficient test data")
            return
        
        heat_id = self.test_heat_ids[2]  # DELETE_TEST_001 (should have no consumption)
        
        try:
            response = self.session.delete(f"{BASE_URL}/heat/{heat_id}")
            if response.status_code == 200:
                self.log_test("Delete Heat - No Consumption", True, "Heat deleted successfully")
                
                # Verify heat is actually deleted
                response = self.session.get(f"{BASE_URL}/heats")
                if response.status_code == 200:
                    heats = response.json()
                    deleted_heat = next((h for h in heats if h.get('id') == heat_id), None)
                    if deleted_heat is None:
                        self.log_test("Verify Heat Deletion", True, "Heat successfully removed from database")
                    else:
                        self.log_test("Verify Heat Deletion", False, "Heat still exists in database")
                else:
                    self.log_test("Verify Heat Deletion", False, "Failed to verify deletion")
            else:
                self.log_test("Delete Heat - No Consumption", False, 
                            f"Failed with status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Delete Heat - No Consumption", False, f"Request failed: {str(e)}")
    
    def test_heat_deletion_with_consumption(self):
        """Test deleting heat with consumption (should fail)"""
        print("\n=== TESTING HEAT DELETION - WITH CONSUMPTION ===")
        
        if len(self.test_heat_ids) < 4:
            self.log_test("Heat Deletion With Consumption", False, "Insufficient test data")
            return
        
        heat_id = self.test_heat_ids[3]  # CONSUME_TEST_001 (already has consumption from previous test)
        
        try:
            response = self.session.delete(f"{BASE_URL}/heat/{heat_id}")
            if response.status_code == 400:
                self.log_test("Delete Heat - With Consumption", True, 
                            "Heat deletion correctly rejected due to consumption")
            else:
                self.log_test("Delete Heat - With Consumption", False, 
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Delete Heat - With Consumption", False, f"Request failed: {str(e)}")
    
    def test_heat_deletion_edge_cases(self):
        """Test edge cases for heat deletion"""
        print("\n=== TESTING HEAT DELETION - EDGE CASES ===")
        
        # Test 1: Delete non-existent heat
        fake_heat_id = "non-existent-id"
        
        try:
            response = self.session.delete(f"{BASE_URL}/heat/{fake_heat_id}")
            if response.status_code == 404:
                self.log_test("Delete Non-existent Heat", True, "Non-existent heat correctly rejected")
            else:
                self.log_test("Delete Non-existent Heat", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Delete Non-existent Heat", False, f"Request failed: {str(e)}")
    
    def test_business_logic_workflow(self):
        """Test complete business logic workflow"""
        print("\n=== TESTING BUSINESS LOGIC WORKFLOW ===")
        
        # Step 1: Add a new heat
        workflow_heat = {
            "heat_number": "WORKFLOW_TEST_001",
            "steel_type": "20.64mm",
            "quantity_kg": 400.0,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=workflow_heat)
            if response.status_code == 200:
                workflow_heat_id = response.json().get('id')
                self.log_test("Workflow - Add Heat", True, f"Heat added with ID: {workflow_heat_id}")
                
                # Step 2: Record production to consume some material
                production_data = {
                    "date": date.today().isoformat(),
                    "product_type": "MK-III",
                    "quantity_produced": 50  # Should consume 46.5kg
                }
                
                response = self.session.post(f"{BASE_URL}/production", json=production_data)
                if response.status_code == 200:
                    self.log_test("Workflow - Record Production", True, "Production recorded successfully")
                    
                    # Step 3: Try to update heat quantity below consumed amount (should fail)
                    update_data = {
                        "heat_number": "WORKFLOW_TEST_001_UPDATED",
                        "steel_type": "20.64mm",
                        "quantity_kg": 30.0  # Less than consumed (46.5kg)
                    }
                    
                    response = self.session.put(f"{BASE_URL}/heat/{workflow_heat_id}", json=update_data)
                    if response.status_code == 400:
                        self.log_test("Workflow - Update Below Consumed", True, 
                                    "Update correctly rejected when quantity below consumed")
                    else:
                        self.log_test("Workflow - Update Below Consumed", False, 
                                    f"Expected 400, got {response.status_code}")
                    
                    # Step 4: Try to delete the heat (should fail due to consumption)
                    response = self.session.delete(f"{BASE_URL}/heat/{workflow_heat_id}")
                    if response.status_code == 400:
                        self.log_test("Workflow - Delete With Consumption", True, 
                                    "Delete correctly rejected due to consumption")
                    else:
                        self.log_test("Workflow - Delete With Consumption", False, 
                                    f"Expected 400, got {response.status_code}")
                    
                else:
                    self.log_test("Workflow - Record Production", False, 
                                f"Production failed: {response.status_code}")
            else:
                self.log_test("Workflow - Add Heat", False, f"Heat creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("Business Logic Workflow", False, f"Request failed: {str(e)}")
        
        # Step 5: Add another heat and delete it immediately (should succeed)
        immediate_delete_heat = {
            "heat_number": "IMMEDIATE_DELETE_001",
            "steel_type": "23mm",
            "quantity_kg": 200.0,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=immediate_delete_heat)
            if response.status_code == 200:
                immediate_heat_id = response.json().get('id')
                self.log_test("Workflow - Add Heat for Immediate Delete", True, 
                            f"Heat added with ID: {immediate_heat_id}")
                
                # Immediately delete it
                response = self.session.delete(f"{BASE_URL}/heat/{immediate_heat_id}")
                if response.status_code == 200:
                    self.log_test("Workflow - Immediate Delete", True, 
                                "Heat deleted successfully (no consumption)")
                else:
                    self.log_test("Workflow - Immediate Delete", False, 
                                f"Delete failed: {response.status_code}")
            else:
                self.log_test("Workflow - Add Heat for Immediate Delete", False, 
                            f"Heat creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("Workflow - Immediate Delete", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Heat Edit/Delete Functionality Testing")
        print("=" * 60)
        
        # Setup test data
        self.setup_test_data()
        
        # Run all test suites
        self.test_heat_update_basic()
        self.test_heat_update_duplicate_number()
        self.test_heat_update_with_consumption()
        self.test_heat_update_edge_cases()
        self.test_heat_deletion_basic()
        self.test_heat_deletion_with_consumption()
        self.test_heat_deletion_edge_cases()
        self.test_business_logic_workflow()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 HEAT EDIT/DELETE TEST SUMMARY")
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
    tester = HeatEditDeleteTester()
    results = tester.run_all_tests()