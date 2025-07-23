#!/usr/bin/env python3
"""
Production Deletion Functionality Testing for Steel Inventory Management System
Tests the new DELETE /api/production/{production_id} endpoint and material restoration logic.
"""

import requests
import json
from datetime import date, datetime
import time

# API Configuration
BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

class ProductionDeletionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_heats = []
        self.created_productions = []
        
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
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test productions
        for production_id in self.created_productions:
            try:
                response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                if response.status_code == 200:
                    print(f"   Deleted production: {production_id}")
            except:
                pass
        
        # Delete test heats (only if no material consumed)
        for heat_id in self.created_heats:
            try:
                response = self.session.delete(f"{BASE_URL}/heat/{heat_id}")
                if response.status_code == 200:
                    print(f"   Deleted heat: {heat_id}")
            except:
                pass
    
    def create_test_heat(self, heat_number, steel_type, quantity_kg):
        """Helper method to create a test heat"""
        heat_data = {
            "heat_number": heat_number,
            "steel_type": steel_type,
            "quantity_kg": quantity_kg,
            "date_received": date.today().isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=heat_data)
            if response.status_code == 200:
                heat_result = response.json()
                heat_id = heat_result.get('id')
                self.created_heats.append(heat_id)
                return heat_result
            else:
                print(f"Failed to create test heat: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating test heat: {str(e)}")
            return None
    
    def create_test_production(self, product_type, quantity_produced):
        """Helper method to create a test production"""
        production_data = {
            "date": date.today().isoformat(),
            "product_type": product_type,
            "quantity_produced": quantity_produced
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/production", json=production_data)
            if response.status_code == 200:
                production_result = response.json()
                production_id = production_result.get('id')
                self.created_productions.append(production_id)
                return production_result
            else:
                print(f"Failed to create test production: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating test production: {str(e)}")
            return None
    
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
    
    def get_heat_details(self, heat_id):
        """Helper method to get heat details"""
        try:
            response = self.session.get(f"{BASE_URL}/heats")
            if response.status_code == 200:
                heats = response.json()
                for heat in heats:
                    if heat.get('id') == heat_id:
                        return heat
            return None
        except Exception as e:
            print(f"Error getting heat details: {str(e)}")
            return None
    
    def test_basic_production_deletion(self):
        """Test 1: Basic production deletion and material restoration"""
        print("\n=== TEST 1: BASIC PRODUCTION DELETION ===")
        
        # Create a test heat
        heat = self.create_test_heat("H_DEL_001", "20.64mm", 1000.0)
        if not heat:
            self.log_test("Basic Deletion - Setup", False, "Failed to create test heat")
            return
        
        heat_id = heat.get('id')
        initial_remaining = heat.get('remaining_kg')
        
        # Record production to consume material
        production = self.create_test_production("MK-III", 100)  # Should consume 93kg
        if not production:
            self.log_test("Basic Deletion - Setup", False, "Failed to create test production")
            return
        
        production_id = production.get('id')
        material_consumed = production.get('material_consumed_kg')
        
        # Verify material was consumed
        heat_after_production = self.get_heat_details(heat_id)
        if heat_after_production:
            remaining_after_production = heat_after_production.get('remaining_kg')
            expected_remaining = initial_remaining - material_consumed
            
            if abs(remaining_after_production - expected_remaining) < 0.01:
                self.log_test("Basic Deletion - Material Consumption", True, 
                            f"Material correctly consumed: {material_consumed}kg")
            else:
                self.log_test("Basic Deletion - Material Consumption", False, 
                            f"Material consumption error. Expected: {expected_remaining}kg, Got: {remaining_after_production}kg")
        
        # Now delete the production record
        try:
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                deletion_result = response.json()
                material_restored = deletion_result.get('material_restored_kg', 0)
                
                self.log_test("Basic Deletion - Delete Request", True, 
                            f"Production deleted successfully. Material restored: {material_restored}kg")
                
                # Verify material was restored to heat
                heat_after_deletion = self.get_heat_details(heat_id)
                if heat_after_deletion:
                    remaining_after_deletion = heat_after_deletion.get('remaining_kg')
                    
                    if abs(remaining_after_deletion - initial_remaining) < 0.01:
                        self.log_test("Basic Deletion - Material Restoration", True, 
                                    f"Material correctly restored. Heat back to {remaining_after_deletion}kg")
                    else:
                        self.log_test("Basic Deletion - Material Restoration", False, 
                                    f"Material restoration error. Expected: {initial_remaining}kg, Got: {remaining_after_deletion}kg")
                else:
                    self.log_test("Basic Deletion - Material Restoration", False, "Could not verify heat after deletion")
                
            else:
                self.log_test("Basic Deletion - Delete Request", False, 
                            f"Failed to delete production: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Basic Deletion - Delete Request", False, f"Request failed: {str(e)}")
    
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
    
    def test_fifo_material_restoration(self):
        """Test 3: Verify material is restored to correct heats in FIFO order"""
        print("\n=== TEST 3: FIFO MATERIAL RESTORATION ===")
        
        # Create multiple heats with different dates
        heat1 = self.create_test_heat("H_FIFO_001", "20.64mm", 300.0)
        time.sleep(1)  # Ensure different timestamps
        heat2 = self.create_test_heat("H_FIFO_002", "20.64mm", 300.0)
        time.sleep(1)
        heat3 = self.create_test_heat("H_FIFO_003", "20.64mm", 300.0)
        
        if not all([heat1, heat2, heat3]):
            self.log_test("FIFO Restoration - Setup", False, "Failed to create test heats")
            return
        
        # Record production that consumes material from multiple heats
        # 400 clips * 0.930kg = 372kg (should consume all of heat1 and 72kg from heat2)
        production = self.create_test_production("MK-III", 400)
        if not production:
            self.log_test("FIFO Restoration - Setup", False, "Failed to create test production")
            return
        
        production_id = production.get('id')
        material_consumed = production.get('material_consumed_kg')
        
        # Verify FIFO consumption
        heat1_after = self.get_heat_details(heat1.get('id'))
        heat2_after = self.get_heat_details(heat2.get('id'))
        heat3_after = self.get_heat_details(heat3.get('id'))
        
        if heat1_after and heat2_after and heat3_after:
            # Heat1 should be fully consumed (0kg remaining)
            # Heat2 should have 228kg remaining (300 - 72)
            # Heat3 should be untouched (300kg remaining)
            
            if (abs(heat1_after.get('remaining_kg', 0) - 0) < 0.01 and
                abs(heat2_after.get('remaining_kg', 0) - 228) < 0.01 and
                abs(heat3_after.get('remaining_kg', 0) - 300) < 0.01):
                self.log_test("FIFO Restoration - FIFO Consumption", True, 
                            "FIFO consumption working correctly")
            else:
                self.log_test("FIFO Restoration - FIFO Consumption", False, 
                            f"FIFO consumption error. Heat1: {heat1_after.get('remaining_kg')}kg, "
                            f"Heat2: {heat2_after.get('remaining_kg')}kg, Heat3: {heat3_after.get('remaining_kg')}kg")
        
        # Now delete the production and verify restoration
        try:
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                deletion_result = response.json()
                material_restored = deletion_result.get('material_restored_kg', 0)
                
                # Verify material was restored in FIFO order
                heat1_restored = self.get_heat_details(heat1.get('id'))
                heat2_restored = self.get_heat_details(heat2.get('id'))
                heat3_restored = self.get_heat_details(heat3.get('id'))
                
                if heat1_restored and heat2_restored and heat3_restored:
                    # After restoration:
                    # Heat1 should be back to 300kg
                    # Heat2 should be back to 300kg
                    # Heat3 should still be 300kg
                    
                    if (abs(heat1_restored.get('remaining_kg', 0) - 300) < 0.01 and
                        abs(heat2_restored.get('remaining_kg', 0) - 300) < 0.01 and
                        abs(heat3_restored.get('remaining_kg', 0) - 300) < 0.01):
                        self.log_test("FIFO Restoration - Material Restoration", True, 
                                    f"Material correctly restored in FIFO order. Restored: {material_restored}kg")
                    else:
                        self.log_test("FIFO Restoration - Material Restoration", False, 
                                    f"FIFO restoration error. Heat1: {heat1_restored.get('remaining_kg')}kg, "
                                    f"Heat2: {heat2_restored.get('remaining_kg')}kg, Heat3: {heat3_restored.get('remaining_kg')}kg")
                else:
                    self.log_test("FIFO Restoration - Material Restoration", False, 
                                "Could not verify heats after restoration")
                
            else:
                self.log_test("FIFO Restoration - Delete Request", False, 
                            f"Failed to delete production: {response.status_code}")
        except Exception as e:
            self.log_test("FIFO Restoration - Delete Request", False, f"Request failed: {str(e)}")
    
    def test_inventory_levels_after_deletion(self):
        """Test 4: Verify total inventory levels are correct after deletion"""
        print("\n=== TEST 4: INVENTORY LEVELS AFTER DELETION ===")
        
        # Get initial inventory status
        initial_inventory = self.get_inventory_status("23mm")
        if not initial_inventory:
            self.log_test("Inventory Levels - Setup", False, "Could not get initial inventory")
            return
        
        initial_stock = initial_inventory.get('current_stock_kg', 0)
        
        # Create a test heat
        heat = self.create_test_heat("H_INV_001", "23mm", 500.0)
        if not heat:
            self.log_test("Inventory Levels - Setup", False, "Failed to create test heat")
            return
        
        # Record production
        production = self.create_test_production("MK-V", 100)  # Should consume 115kg
        if not production:
            self.log_test("Inventory Levels - Setup", False, "Failed to create test production")
            return
        
        production_id = production.get('id')
        material_consumed = production.get('material_consumed_kg')
        
        # Check inventory after production
        inventory_after_production = self.get_inventory_status("23mm")
        if inventory_after_production:
            stock_after_production = inventory_after_production.get('current_stock_kg', 0)
            expected_stock = initial_stock + 500.0 - material_consumed
            
            if abs(stock_after_production - expected_stock) < 0.01:
                self.log_test("Inventory Levels - After Production", True, 
                            f"Inventory correct after production: {stock_after_production}kg")
            else:
                self.log_test("Inventory Levels - After Production", False, 
                            f"Inventory error after production. Expected: {expected_stock}kg, Got: {stock_after_production}kg")
        
        # Delete production
        try:
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                # Check inventory after deletion
                inventory_after_deletion = self.get_inventory_status("23mm")
                if inventory_after_deletion:
                    stock_after_deletion = inventory_after_deletion.get('current_stock_kg', 0)
                    expected_final_stock = initial_stock + 500.0  # Should be back to initial + new heat
                    
                    if abs(stock_after_deletion - expected_final_stock) < 0.01:
                        self.log_test("Inventory Levels - After Deletion", True, 
                                    f"Inventory correctly restored after deletion: {stock_after_deletion}kg")
                    else:
                        self.log_test("Inventory Levels - After Deletion", False, 
                                    f"Inventory error after deletion. Expected: {expected_final_stock}kg, Got: {stock_after_deletion}kg")
                else:
                    self.log_test("Inventory Levels - After Deletion", False, 
                                "Could not get inventory after deletion")
            else:
                self.log_test("Inventory Levels - Delete Request", False, 
                            f"Failed to delete production: {response.status_code}")
        except Exception as e:
            self.log_test("Inventory Levels - Delete Request", False, f"Request failed: {str(e)}")
    
    def test_dashboard_data_after_deletion(self):
        """Test 5: Test that dashboard data reflects the restored material"""
        print("\n=== TEST 5: DASHBOARD DATA AFTER DELETION ===")
        
        # Get initial dashboard data
        try:
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                initial_dashboard = response.json()
                initial_mkiii_total = initial_dashboard.get('total_production_mkiii', 0)
                initial_mkv_total = initial_dashboard.get('total_production_mkv', 0)
            else:
                self.log_test("Dashboard Data - Setup", False, "Could not get initial dashboard data")
                return
        except Exception as e:
            self.log_test("Dashboard Data - Setup", False, f"Request failed: {str(e)}")
            return
        
        # Create test heat and production
        heat = self.create_test_heat("H_DASH_001", "20.64mm", 200.0)
        if not heat:
            self.log_test("Dashboard Data - Setup", False, "Failed to create test heat")
            return
        
        production = self.create_test_production("MK-III", 50)
        if not production:
            self.log_test("Dashboard Data - Setup", False, "Failed to create test production")
            return
        
        production_id = production.get('id')
        
        # Check dashboard after production
        try:
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                dashboard_after_production = response.json()
                mkiii_after_production = dashboard_after_production.get('total_production_mkiii', 0)
                
                if mkiii_after_production == initial_mkiii_total + 50:
                    self.log_test("Dashboard Data - After Production", True, 
                                f"Dashboard correctly updated after production: {mkiii_after_production} total MK-III")
                else:
                    self.log_test("Dashboard Data - After Production", False, 
                                f"Dashboard error after production. Expected: {initial_mkiii_total + 50}, Got: {mkiii_after_production}")
            else:
                self.log_test("Dashboard Data - After Production", False, 
                            f"Failed to get dashboard after production: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Data - After Production", False, f"Request failed: {str(e)}")
        
        # Delete production and check dashboard
        try:
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                # Check dashboard after deletion
                response = self.session.get(f"{BASE_URL}/dashboard")
                if response.status_code == 200:
                    dashboard_after_deletion = response.json()
                    mkiii_after_deletion = dashboard_after_deletion.get('total_production_mkiii', 0)
                    
                    if mkiii_after_deletion == initial_mkiii_total:
                        self.log_test("Dashboard Data - After Deletion", True, 
                                    f"Dashboard correctly updated after deletion: {mkiii_after_deletion} total MK-III")
                    else:
                        self.log_test("Dashboard Data - After Deletion", False, 
                                    f"Dashboard error after deletion. Expected: {initial_mkiii_total}, Got: {mkiii_after_deletion}")
                else:
                    self.log_test("Dashboard Data - After Deletion", False, 
                                f"Failed to get dashboard after deletion: {response.status_code}")
            else:
                self.log_test("Dashboard Data - Delete Request", False, 
                            f"Failed to delete production: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Data - Delete Request", False, f"Request failed: {str(e)}")
    
    def test_edge_case_no_heats_for_restoration(self):
        """Test 6: Delete production when no heats exist for restoration"""
        print("\n=== TEST 6: EDGE CASE - NO HEATS FOR RESTORATION ===")
        
        # This test is complex because we need to create a scenario where
        # a production exists but the heats it consumed from are deleted
        # For now, we'll test the API's response to this scenario
        
        # Create a heat and production
        heat = self.create_test_heat("H_EDGE_001", "20.64mm", 100.0)
        if not heat:
            self.log_test("Edge Case - Setup", False, "Failed to create test heat")
            return
        
        production = self.create_test_production("MK-III", 50)  # Consumes 46.5kg
        if not production:
            self.log_test("Edge Case - Setup", False, "Failed to create test production")
            return
        
        production_id = production.get('id')
        heat_id = heat.get('id')
        
        # Try to delete the heat (this should fail because material was consumed)
        try:
            response = self.session.delete(f"{BASE_URL}/heat/{heat_id}")
            if response.status_code == 400:
                self.log_test("Edge Case - Heat Deletion Prevention", True, 
                            "Correctly prevented deletion of heat with consumed material")
            else:
                self.log_test("Edge Case - Heat Deletion Prevention", False, 
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Edge Case - Heat Deletion Prevention", False, f"Request failed: {str(e)}")
        
        # Now delete the production (this should work and restore material)
        try:
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                deletion_result = response.json()
                material_restored = deletion_result.get('material_restored_kg', 0)
                
                self.log_test("Edge Case - Production Deletion", True, 
                            f"Production deleted successfully. Material restored: {material_restored}kg")
            else:
                self.log_test("Edge Case - Production Deletion", False, 
                            f"Failed to delete production: {response.status_code}")
        except Exception as e:
            self.log_test("Edge Case - Production Deletion", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all production deletion tests"""
        print("🚀 Starting Production Deletion Functionality Testing")
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
        
        try:
            # Run all test suites
            self.test_basic_production_deletion()
            self.test_delete_nonexistent_production()
            self.test_fifo_material_restoration()
            self.test_inventory_levels_after_deletion()
            self.test_dashboard_data_after_deletion()
            self.test_edge_case_no_heats_for_restoration()
            
        finally:
            # Always cleanup test data
            self.cleanup_test_data()
        
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
    tester = ProductionDeletionTester()
    results = tester.run_all_tests()