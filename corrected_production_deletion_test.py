#!/usr/bin/env python3
"""
Corrected Production Deletion Functionality Testing for Steel Inventory Management System
Tests the DELETE /api/production/{production_id} endpoint with proper FIFO understanding.
"""

import requests
import json
from datetime import date, datetime
import time

# API Configuration
BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

class CorrectedProductionDeletionTester:
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
    
    def get_inventory_status(self, steel_type):
        """Helper method to get current inventory status for a steel type"""
        try:
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                inventory = response.json()
                for item in inventory:
                    if item.get('steel_type') == steel_type:
                        return item
            return None
        except Exception as e:
            print(f"Error getting inventory status: {str(e)}")
            return None
    
    def get_oldest_heat_with_stock(self, steel_type):
        """Get the oldest heat with remaining stock for a steel type"""
        try:
            response = self.session.get(f"{BASE_URL}/heats")
            if response.status_code == 200:
                heats = response.json()
                # Filter by steel type and remaining stock > 0
                available_heats = [h for h in heats if h.get('steel_type') == steel_type and h.get('remaining_kg', 0) > 0]
                # Sort by date_received (FIFO)
                available_heats.sort(key=lambda x: x.get('date_received', ''))
                return available_heats[0] if available_heats else None
            return None
        except Exception as e:
            print(f"Error getting oldest heat: {str(e)}")
            return None
    
    def test_production_deletion_basic(self):
        """Test 1: Basic production deletion and verify material restoration"""
        print("\n=== TEST 1: BASIC PRODUCTION DELETION ===")
        
        # Get initial inventory status
        initial_inventory = self.get_inventory_status("20.64mm")
        if not initial_inventory:
            self.log_test("Basic Deletion - Setup", False, "Could not get initial inventory")
            return
        
        initial_stock = initial_inventory.get('current_stock_kg', 0)
        initial_consumed = initial_inventory.get('total_consumed_kg', 0)
        
        # Get the oldest heat that will be affected
        oldest_heat = self.get_oldest_heat_with_stock("20.64mm")
        if not oldest_heat:
            self.log_test("Basic Deletion - Setup", False, "No available heat found")
            return
        
        oldest_heat_id = oldest_heat.get('id')
        initial_remaining = oldest_heat.get('remaining_kg', 0)
        
        # Record production
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 50  # Should consume 46.5kg
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=production_data)
            if response.status_code == 200:
                production = response.json()
                production_id = production.get('id')
                material_consumed = production.get('material_consumed_kg')
                
                self.log_test("Basic Deletion - Production Creation", True, 
                            f"Production created successfully. Material consumed: {material_consumed}kg")
                
                # Verify inventory was updated
                inventory_after_production = self.get_inventory_status("20.64mm")
                if inventory_after_production:
                    stock_after_production = inventory_after_production.get('current_stock_kg', 0)
                    consumed_after_production = inventory_after_production.get('total_consumed_kg', 0)
                    
                    expected_stock = initial_stock - material_consumed
                    expected_consumed = initial_consumed + material_consumed
                    
                    if (abs(stock_after_production - expected_stock) < 0.01 and 
                        abs(consumed_after_production - expected_consumed) < 0.01):
                        self.log_test("Basic Deletion - Inventory Update", True, 
                                    f"Inventory correctly updated. Stock: {stock_after_production}kg, Consumed: {consumed_after_production}kg")
                    else:
                        self.log_test("Basic Deletion - Inventory Update", False, 
                                    f"Inventory update error. Expected stock: {expected_stock}kg, Got: {stock_after_production}kg")
                
                # Now delete the production
                response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                if response.status_code == 200:
                    deletion_result = response.json()
                    material_restored = deletion_result.get('material_restored_kg', 0)
                    
                    self.log_test("Basic Deletion - Delete Request", True, 
                                f"Production deleted successfully. Material restored: {material_restored}kg")
                    
                    # Verify inventory was restored
                    inventory_after_deletion = self.get_inventory_status("20.64mm")
                    if inventory_after_deletion:
                        stock_after_deletion = inventory_after_deletion.get('current_stock_kg', 0)
                        consumed_after_deletion = inventory_after_deletion.get('total_consumed_kg', 0)
                        
                        if (abs(stock_after_deletion - initial_stock) < 0.01 and 
                            abs(consumed_after_deletion - initial_consumed) < 0.01):
                            self.log_test("Basic Deletion - Inventory Restoration", True, 
                                        f"Inventory correctly restored. Stock: {stock_after_deletion}kg, Consumed: {consumed_after_deletion}kg")
                        else:
                            self.log_test("Basic Deletion - Inventory Restoration", False, 
                                        f"Inventory restoration error. Expected stock: {initial_stock}kg, Got: {stock_after_deletion}kg")
                    
                else:
                    self.log_test("Basic Deletion - Delete Request", False, 
                                f"Failed to delete production: {response.status_code} - {response.text}")
                
            else:
                self.log_test("Basic Deletion - Production Creation", False, 
                            f"Failed to create production: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Basic Deletion - Request", False, f"Request failed: {str(e)}")
    
    def test_delete_nonexistent_production(self):
        """Test 2: Delete non-existent production record (should return 404)"""
        print("\n=== TEST 2: DELETE NON-EXISTENT PRODUCTION ===")
        
        fake_production_id = "non-existent-id-12345"
        
        try:
            response = self.session.delete(f"{BASE_URL}/production/{fake_production_id}")
            if response.status_code == 404:
                self.log_test("Delete Non-existent Production", True, 
                            "Correctly returned 404 for non-existent production")
            else:
                self.log_test("Delete Non-existent Production", False, 
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Delete Non-existent Production", False, f"Request failed: {str(e)}")
    
    def test_multiple_productions_and_deletions(self):
        """Test 3: Create multiple productions and delete them to verify FIFO restoration"""
        print("\n=== TEST 3: MULTIPLE PRODUCTIONS AND DELETIONS ===")
        
        # Get initial inventory
        initial_inventory = self.get_inventory_status("23mm")
        if not initial_inventory:
            self.log_test("Multiple Deletions - Setup", False, "Could not get initial inventory")
            return
        
        initial_stock = initial_inventory.get('current_stock_kg', 0)
        
        # Create multiple productions
        production_ids = []
        total_material_consumed = 0
        
        for i in range(3):
            production_data = {
                "date": date.today().isoformat(),
                "product_type": "MK-V",
                "quantity_produced": 20  # Each consumes 23kg
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/production", json=production_data)
                if response.status_code == 200:
                    production = response.json()
                    production_ids.append(production.get('id'))
                    total_material_consumed += production.get('material_consumed_kg', 0)
                else:
                    self.log_test("Multiple Deletions - Production Creation", False, 
                                f"Failed to create production {i+1}: {response.status_code}")
                    return
            except Exception as e:
                self.log_test("Multiple Deletions - Production Creation", False, 
                            f"Request failed for production {i+1}: {str(e)}")
                return
        
        self.log_test("Multiple Deletions - Production Creation", True, 
                    f"Created 3 productions consuming total {total_material_consumed}kg")
        
        # Verify inventory after productions
        inventory_after_productions = self.get_inventory_status("23mm")
        if inventory_after_productions:
            stock_after_productions = inventory_after_productions.get('current_stock_kg', 0)
            expected_stock = initial_stock - total_material_consumed
            
            if abs(stock_after_productions - expected_stock) < 0.01:
                self.log_test("Multiple Deletions - Inventory After Productions", True, 
                            f"Inventory correctly updated: {stock_after_productions}kg")
            else:
                self.log_test("Multiple Deletions - Inventory After Productions", False, 
                            f"Inventory error. Expected: {expected_stock}kg, Got: {stock_after_productions}kg")
        
        # Delete all productions
        total_material_restored = 0
        for i, production_id in enumerate(production_ids):
            try:
                response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                if response.status_code == 200:
                    deletion_result = response.json()
                    material_restored = deletion_result.get('material_restored_kg', 0)
                    total_material_restored += material_restored
                else:
                    self.log_test("Multiple Deletions - Delete Productions", False, 
                                f"Failed to delete production {i+1}: {response.status_code}")
                    return
            except Exception as e:
                self.log_test("Multiple Deletions - Delete Productions", False, 
                            f"Request failed for deletion {i+1}: {str(e)}")
                return
        
        self.log_test("Multiple Deletions - Delete Productions", True, 
                    f"Deleted all productions, restored total {total_material_restored}kg")
        
        # Verify inventory after deletions
        inventory_after_deletions = self.get_inventory_status("23mm")
        if inventory_after_deletions:
            stock_after_deletions = inventory_after_deletions.get('current_stock_kg', 0)
            
            if abs(stock_after_deletions - initial_stock) < 0.01:
                self.log_test("Multiple Deletions - Final Inventory", True, 
                            f"Inventory correctly restored: {stock_after_deletions}kg")
            else:
                self.log_test("Multiple Deletions - Final Inventory", False, 
                            f"Inventory restoration error. Expected: {initial_stock}kg, Got: {stock_after_deletions}kg")
    
    def test_dashboard_totals_after_deletion(self):
        """Test 4: Verify dashboard production totals are updated after deletion"""
        print("\n=== TEST 4: DASHBOARD TOTALS AFTER DELETION ===")
        
        # Get initial dashboard data
        try:
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                initial_dashboard = response.json()
                initial_mkiii_total = initial_dashboard.get('total_production_mkiii', 0)
            else:
                self.log_test("Dashboard Totals - Setup", False, "Could not get initial dashboard data")
                return
        except Exception as e:
            self.log_test("Dashboard Totals - Setup", False, f"Request failed: {str(e)}")
            return
        
        # Create production
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 25
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=production_data)
            if response.status_code == 200:
                production = response.json()
                production_id = production.get('id')
                
                # Check dashboard after production
                response = self.session.get(f"{BASE_URL}/dashboard")
                if response.status_code == 200:
                    dashboard_after_production = response.json()
                    mkiii_after_production = dashboard_after_production.get('total_production_mkiii', 0)
                    
                    if mkiii_after_production == initial_mkiii_total + 25:
                        self.log_test("Dashboard Totals - After Production", True, 
                                    f"Dashboard correctly updated: {mkiii_after_production} total MK-III")
                    else:
                        self.log_test("Dashboard Totals - After Production", False, 
                                    f"Dashboard error. Expected: {initial_mkiii_total + 25}, Got: {mkiii_after_production}")
                
                # Delete production
                response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                if response.status_code == 200:
                    # Check dashboard after deletion
                    response = self.session.get(f"{BASE_URL}/dashboard")
                    if response.status_code == 200:
                        dashboard_after_deletion = response.json()
                        mkiii_after_deletion = dashboard_after_deletion.get('total_production_mkiii', 0)
                        
                        if mkiii_after_deletion == initial_mkiii_total:
                            self.log_test("Dashboard Totals - After Deletion", True, 
                                        f"Dashboard correctly restored: {mkiii_after_deletion} total MK-III")
                        else:
                            self.log_test("Dashboard Totals - After Deletion", False, 
                                        f"Dashboard error. Expected: {initial_mkiii_total}, Got: {mkiii_after_deletion}")
                    else:
                        self.log_test("Dashboard Totals - After Deletion", False, 
                                    f"Failed to get dashboard after deletion: {response.status_code}")
                else:
                    self.log_test("Dashboard Totals - Delete Request", False, 
                                f"Failed to delete production: {response.status_code}")
            else:
                self.log_test("Dashboard Totals - Production Creation", False, 
                            f"Failed to create production: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Totals - Request", False, f"Request failed: {str(e)}")
    
    def test_data_integrity_after_operations(self):
        """Test 5: Verify overall data integrity after multiple operations"""
        print("\n=== TEST 5: DATA INTEGRITY VERIFICATION ===")
        
        # Get initial state
        try:
            # Get initial inventory
            initial_inventory_response = self.session.get(f"{BASE_URL}/inventory")
            initial_dashboard_response = self.session.get(f"{BASE_URL}/dashboard")
            initial_productions_response = self.session.get(f"{BASE_URL}/productions")
            
            if not all([r.status_code == 200 for r in [initial_inventory_response, initial_dashboard_response, initial_productions_response]]):
                self.log_test("Data Integrity - Setup", False, "Could not get initial system state")
                return
            
            initial_inventory = initial_inventory_response.json()
            initial_dashboard = initial_dashboard_response.json()
            initial_productions = initial_productions_response.json()
            
            initial_mkiii_count = len([p for p in initial_productions if p.get('product_type') == 'MK-III'])
            initial_mkv_count = len([p for p in initial_productions if p.get('product_type') == 'MK-V'])
            
            # Perform a series of operations
            operations_log = []
            
            # Create production
            production_data = {
                "date": date.today().isoformat(),
                "product_type": "MK-III",
                "quantity_produced": 10
            }
            
            response = self.session.post(f"{BASE_URL}/production", json=production_data)
            if response.status_code == 200:
                production = response.json()
                production_id = production.get('id')
                operations_log.append(f"Created production: {production_id}")
                
                # Delete production
                response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                if response.status_code == 200:
                    operations_log.append(f"Deleted production: {production_id}")
                    
                    # Verify final state matches initial state
                    final_inventory_response = self.session.get(f"{BASE_URL}/inventory")
                    final_dashboard_response = self.session.get(f"{BASE_URL}/dashboard")
                    final_productions_response = self.session.get(f"{BASE_URL}/productions")
                    
                    if all([r.status_code == 200 for r in [final_inventory_response, final_dashboard_response, final_productions_response]]):
                        final_inventory = final_inventory_response.json()
                        final_dashboard = final_dashboard_response.json()
                        final_productions = final_productions_response.json()
                        
                        final_mkiii_count = len([p for p in final_productions if p.get('product_type') == 'MK-III'])
                        final_mkv_count = len([p for p in final_productions if p.get('product_type') == 'MK-V'])
                        
                        # Check if counts match
                        if (final_mkiii_count == initial_mkiii_count and 
                            final_mkv_count == initial_mkv_count):
                            self.log_test("Data Integrity - Production Counts", True, 
                                        f"Production counts correctly restored: MK-III: {final_mkiii_count}, MK-V: {final_mkv_count}")
                        else:
                            self.log_test("Data Integrity - Production Counts", False, 
                                        f"Production count mismatch. Initial MK-III: {initial_mkiii_count}, Final: {final_mkiii_count}")
                        
                        # Check inventory levels
                        inventory_match = True
                        for i, initial_item in enumerate(initial_inventory):
                            final_item = final_inventory[i] if i < len(final_inventory) else {}
                            if abs(initial_item.get('current_stock_kg', 0) - final_item.get('current_stock_kg', 0)) > 0.01:
                                inventory_match = False
                                break
                        
                        if inventory_match:
                            self.log_test("Data Integrity - Inventory Levels", True, 
                                        "Inventory levels correctly restored")
                        else:
                            self.log_test("Data Integrity - Inventory Levels", False, 
                                        "Inventory levels do not match initial state")
                        
                        # Check dashboard totals
                        if (initial_dashboard.get('total_production_mkiii') == final_dashboard.get('total_production_mkiii') and
                            initial_dashboard.get('total_production_mkv') == final_dashboard.get('total_production_mkv')):
                            self.log_test("Data Integrity - Dashboard Totals", True, 
                                        "Dashboard totals correctly restored")
                        else:
                            self.log_test("Data Integrity - Dashboard Totals", False, 
                                        "Dashboard totals do not match initial state")
                    else:
                        self.log_test("Data Integrity - Final State", False, "Could not get final system state")
                else:
                    self.log_test("Data Integrity - Delete Operation", False, 
                                f"Failed to delete production: {response.status_code}")
            else:
                self.log_test("Data Integrity - Create Operation", False, 
                            f"Failed to create production: {response.status_code}")
                
        except Exception as e:
            self.log_test("Data Integrity - Request", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all production deletion tests"""
        print("🚀 Starting Corrected Production Deletion Functionality Testing")
        print("=" * 70)
        
        # Test API connection first
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print("❌ API connection failed. Stopping tests.")
                return
        except Exception as e:
            print(f"❌ API connection failed: {str(e)}. Stopping tests.")
            return
        
        # Run all test suites
        self.test_production_deletion_basic()
        self.test_delete_nonexistent_production()
        self.test_multiple_productions_and_deletions()
        self.test_dashboard_totals_after_deletion()
        self.test_data_integrity_after_operations()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 PRODUCTION DELETION TEST SUMMARY")
        print("=" * 70)
        
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
    tester = CorrectedProductionDeletionTester()
    results = tester.run_all_tests()