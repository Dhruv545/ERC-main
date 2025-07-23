#!/usr/bin/env python3
"""
Comprehensive Production Deletion Test - Covering all review request requirements
Tests all specific scenarios mentioned in the review request.
"""

import requests
import json
from datetime import date, datetime
import time

BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

class ComprehensiveProductionDeletionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_heats = []
        
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
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        for heat_id in self.created_heats:
            try:
                self.session.delete(f"{BASE_URL}/heat/{heat_id}")
            except:
                pass
    
    def create_test_heat(self, heat_number, steel_type, quantity_kg, date_offset_days=0):
        """Create a test heat with optional date offset"""
        from datetime import timedelta
        heat_date = date.today() - timedelta(days=date_offset_days)
        
        heat_data = {
            "heat_number": heat_number,
            "steel_type": steel_type,
            "quantity_kg": quantity_kg,
            "date_received": heat_date.isoformat()
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/heat", json=heat_data)
            if response.status_code == 200:
                heat_result = response.json()
                heat_id = heat_result.get('id')
                self.created_heats.append(heat_id)
                return heat_result
            return None
        except:
            return None
    
    def test_requirement_1_basic_deletion(self):
        """Requirement 1: Delete a production record and verify material is restored to inventory"""
        print("\n=== REQUIREMENT 1: BASIC PRODUCTION DELETION ===")
        
        # Create a dedicated heat for this test
        test_heat = self.create_test_heat("REQ1_HEAT", "20.64mm", 1000.0, date_offset_days=10)
        if not test_heat:
            self.log_test("Req1 - Setup", False, "Failed to create test heat")
            return
        
        # Get initial inventory
        response = self.session.get(f"{BASE_URL}/inventory")
        initial_inventory = response.json() if response.status_code == 200 else []
        initial_stock_20_64 = next((item['current_stock_kg'] for item in initial_inventory 
                                  if item['steel_type'] == '20.64mm'), 0)
        
        # Record production
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 100  # Should consume 93kg
        }
        
        response = self.session.post(f"{BASE_URL}/production", json=production_data)
        if response.status_code == 200:
            production = response.json()
            production_id = production.get('id')
            material_consumed = production.get('material_consumed_kg')
            
            # Verify material was consumed
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                inventory_after = response.json()
                stock_after = next((item['current_stock_kg'] for item in inventory_after 
                                  if item['steel_type'] == '20.64mm'), 0)
                
                if abs(stock_after - (initial_stock_20_64 - material_consumed)) < 0.01:
                    self.log_test("Req1 - Material Consumption", True, 
                                f"Material correctly consumed: {material_consumed}kg")
                    
                    # Now delete the production
                    response = self.session.delete(f"{BASE_URL}/production/{production_id}")
                    if response.status_code == 200:
                        deletion_result = response.json()
                        material_restored = deletion_result.get('material_restored_kg', 0)
                        
                        # Verify material was restored
                        response = self.session.get(f"{BASE_URL}/inventory")
                        if response.status_code == 200:
                            final_inventory = response.json()
                            final_stock = next((item['current_stock_kg'] for item in final_inventory 
                                              if item['steel_type'] == '20.64mm'), 0)
                            
                            if abs(final_stock - initial_stock_20_64) < 0.01:
                                self.log_test("Req1 - Material Restoration", True, 
                                            f"Material correctly restored: {material_restored}kg")
                            else:
                                self.log_test("Req1 - Material Restoration", False, 
                                            f"Material restoration failed. Expected: {initial_stock_20_64}kg, Got: {final_stock}kg")
                        else:
                            self.log_test("Req1 - Final Inventory Check", False, "Could not verify final inventory")
                    else:
                        self.log_test("Req1 - Production Deletion", False, 
                                    f"Failed to delete production: {response.status_code}")
                else:
                    self.log_test("Req1 - Material Consumption", False, 
                                f"Material consumption failed. Expected: {initial_stock_20_64 - material_consumed}kg, Got: {stock_after}kg")
            else:
                self.log_test("Req1 - Inventory Check", False, "Could not verify inventory after production")
        else:
            self.log_test("Req1 - Production Creation", False, f"Failed to create production: {response.status_code}")
    
    def test_requirement_2_nonexistent_production(self):
        """Requirement 2: Test deleting non-existent production record (should return 404)"""
        print("\n=== REQUIREMENT 2: DELETE NON-EXISTENT PRODUCTION ===")
        
        fake_id = "fake-production-id-123456789"
        
        try:
            response = self.session.delete(f"{BASE_URL}/production/{fake_id}")
            if response.status_code == 404:
                self.log_test("Req2 - 404 Response", True, "Correctly returned 404 for non-existent production")
            else:
                self.log_test("Req2 - 404 Response", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Req2 - Request", False, f"Request failed: {str(e)}")
    
    def test_requirement_3_fifo_restoration(self):
        """Requirement 3: Verify that material is restored to the correct heats in FIFO order"""
        print("\n=== REQUIREMENT 3: FIFO MATERIAL RESTORATION ===")
        
        # Create multiple heats with different dates (older first)
        heat1 = self.create_test_heat("FIFO_HEAT_1", "23mm", 200.0, date_offset_days=5)
        time.sleep(1)
        heat2 = self.create_test_heat("FIFO_HEAT_2", "23mm", 200.0, date_offset_days=3)
        time.sleep(1)
        heat3 = self.create_test_heat("FIFO_HEAT_3", "23mm", 200.0, date_offset_days=1)
        
        if not all([heat1, heat2, heat3]):
            self.log_test("Req3 - Setup", False, "Failed to create test heats")
            return
        
        # Record production that will consume from multiple heats
        # 200 MK-V clips = 230kg (will consume all of heat1 and 30kg from heat2)
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-V",
            "quantity_produced": 200
        }
        
        response = self.session.post(f"{BASE_URL}/production", json=production_data)
        if response.status_code == 200:
            production = response.json()
            production_id = production.get('id')
            material_consumed = production.get('material_consumed_kg')
            
            self.log_test("Req3 - Production Creation", True, 
                        f"Production created, consuming {material_consumed}kg")
            
            # Get heat states after production (to verify FIFO consumption)
            response = self.session.get(f"{BASE_URL}/heats")
            if response.status_code == 200:
                heats_after = response.json()
                heat1_after = next((h for h in heats_after if h['id'] == heat1['id']), None)
                heat2_after = next((h for h in heats_after if h['id'] == heat2['id']), None)
                heat3_after = next((h for h in heats_after if h['id'] == heat3['id']), None)
                
                # Verify FIFO consumption pattern
                fifo_correct = True
                if heat1_after and heat1_after.get('remaining_kg', 0) > 0:
                    # Heat1 should be fully consumed first
                    fifo_correct = False
                
                if heat3_after and heat3_after.get('remaining_kg', 0) < 200:
                    # Heat3 should be untouched if heat1 and heat2 had enough material
                    fifo_correct = False
                
                if fifo_correct:
                    self.log_test("Req3 - FIFO Consumption", True, "FIFO consumption working correctly")
                else:
                    self.log_test("Req3 - FIFO Consumption", False, 
                                f"FIFO consumption error. Heat1: {heat1_after.get('remaining_kg') if heat1_after else 'N/A'}kg, "
                                f"Heat2: {heat2_after.get('remaining_kg') if heat2_after else 'N/A'}kg, "
                                f"Heat3: {heat3_after.get('remaining_kg') if heat3_after else 'N/A'}kg")
            
            # Now delete the production and verify FIFO restoration
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                deletion_result = response.json()
                material_restored = deletion_result.get('material_restored_kg', 0)
                
                self.log_test("Req3 - Production Deletion", True, 
                            f"Production deleted, restored {material_restored}kg")
                
                # Verify material was restored in FIFO order
                response = self.session.get(f"{BASE_URL}/heats")
                if response.status_code == 200:
                    heats_final = response.json()
                    heat1_final = next((h for h in heats_final if h['id'] == heat1['id']), None)
                    heat2_final = next((h for h in heats_final if h['id'] == heat2['id']), None)
                    heat3_final = next((h for h in heats_final if h['id'] == heat3['id']), None)
                    
                    # All heats should be back to their original quantities
                    restoration_correct = (
                        heat1_final and abs(heat1_final.get('remaining_kg', 0) - 200) < 0.01 and
                        heat2_final and abs(heat2_final.get('remaining_kg', 0) - 200) < 0.01 and
                        heat3_final and abs(heat3_final.get('remaining_kg', 0) - 200) < 0.01
                    )
                    
                    if restoration_correct:
                        self.log_test("Req3 - FIFO Restoration", True, "Material correctly restored in FIFO order")
                    else:
                        self.log_test("Req3 - FIFO Restoration", False, 
                                    f"FIFO restoration error. Heat1: {heat1_final.get('remaining_kg') if heat1_final else 'N/A'}kg, "
                                    f"Heat2: {heat2_final.get('remaining_kg') if heat2_final else 'N/A'}kg, "
                                    f"Heat3: {heat3_final.get('remaining_kg') if heat3_final else 'N/A'}kg")
                else:
                    self.log_test("Req3 - Final Heat Check", False, "Could not verify final heat states")
            else:
                self.log_test("Req3 - Production Deletion", False, f"Failed to delete production: {response.status_code}")
        else:
            self.log_test("Req3 - Production Creation", False, f"Failed to create production: {response.status_code}")
    
    def test_requirement_4_business_logic(self):
        """Requirement 4: Test business logic - inventory levels and dashboard data"""
        print("\n=== REQUIREMENT 4: BUSINESS LOGIC VERIFICATION ===")
        
        # Get initial states
        initial_inventory_response = self.session.get(f"{BASE_URL}/inventory")
        initial_dashboard_response = self.session.get(f"{BASE_URL}/dashboard")
        
        if not all([r.status_code == 200 for r in [initial_inventory_response, initial_dashboard_response]]):
            self.log_test("Req4 - Setup", False, "Could not get initial system state")
            return
        
        initial_inventory = initial_inventory_response.json()
        initial_dashboard = initial_dashboard_response.json()
        
        initial_stock_mkiii = next((item['current_stock_kg'] for item in initial_inventory 
                                  if item['steel_type'] == '20.64mm'), 0)
        initial_mkiii_total = initial_dashboard.get('total_production_mkiii', 0)
        
        # Create and record production
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 75  # Should consume 69.75kg
        }
        
        response = self.session.post(f"{BASE_URL}/production", json=production_data)
        if response.status_code == 200:
            production = response.json()
            production_id = production.get('id')
            material_consumed = production.get('material_consumed_kg')
            
            # Verify inventory levels after production
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                inventory_after = response.json()
                stock_after = next((item['current_stock_kg'] for item in inventory_after 
                                  if item['steel_type'] == '20.64mm'), 0)
                
                expected_stock = initial_stock_mkiii - material_consumed
                if abs(stock_after - expected_stock) < 0.01:
                    self.log_test("Req4 - Inventory Levels After Production", True, 
                                f"Inventory correctly updated: {stock_after}kg")
                else:
                    self.log_test("Req4 - Inventory Levels After Production", False, 
                                f"Inventory error. Expected: {expected_stock}kg, Got: {stock_after}kg")
            
            # Verify dashboard data after production
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                dashboard_after = response.json()
                mkiii_total_after = dashboard_after.get('total_production_mkiii', 0)
                
                if mkiii_total_after == initial_mkiii_total + 75:
                    self.log_test("Req4 - Dashboard Data After Production", True, 
                                f"Dashboard correctly updated: {mkiii_total_after} total MK-III")
                else:
                    self.log_test("Req4 - Dashboard Data After Production", False, 
                                f"Dashboard error. Expected: {initial_mkiii_total + 75}, Got: {mkiii_total_after}")
            
            # Delete production
            response = self.session.delete(f"{BASE_URL}/production/{production_id}")
            if response.status_code == 200:
                # Verify inventory levels after deletion
                response = self.session.get(f"{BASE_URL}/inventory")
                if response.status_code == 200:
                    final_inventory = response.json()
                    final_stock = next((item['current_stock_kg'] for item in final_inventory 
                                      if item['steel_type'] == '20.64mm'), 0)
                    
                    if abs(final_stock - initial_stock_mkiii) < 0.01:
                        self.log_test("Req4 - Inventory Levels After Deletion", True, 
                                    f"Inventory correctly restored: {final_stock}kg")
                    else:
                        self.log_test("Req4 - Inventory Levels After Deletion", False, 
                                    f"Inventory restoration error. Expected: {initial_stock_mkiii}kg, Got: {final_stock}kg")
                
                # Verify dashboard data after deletion
                response = self.session.get(f"{BASE_URL}/dashboard")
                if response.status_code == 200:
                    final_dashboard = response.json()
                    final_mkiii_total = final_dashboard.get('total_production_mkiii', 0)
                    
                    if final_mkiii_total == initial_mkiii_total:
                        self.log_test("Req4 - Dashboard Data After Deletion", True, 
                                    f"Dashboard correctly restored: {final_mkiii_total} total MK-III")
                    else:
                        self.log_test("Req4 - Dashboard Data After Deletion", False, 
                                    f"Dashboard restoration error. Expected: {initial_mkiii_total}, Got: {final_mkiii_total}")
                else:
                    self.log_test("Req4 - Final Dashboard Check", False, "Could not verify final dashboard")
            else:
                self.log_test("Req4 - Production Deletion", False, f"Failed to delete production: {response.status_code}")
        else:
            self.log_test("Req4 - Production Creation", False, f"Failed to create production: {response.status_code}")
    
    def test_requirement_5_edge_cases(self):
        """Requirement 5: Test edge cases and error handling"""
        print("\n=== REQUIREMENT 5: EDGE CASES AND ERROR HANDLING ===")
        
        # Test 1: Delete production with invalid ID format
        invalid_ids = ["", "invalid-id", "12345", None]
        
        for i, invalid_id in enumerate(invalid_ids):
            if invalid_id is None:
                continue
            try:
                response = self.session.delete(f"{BASE_URL}/production/{invalid_id}")
                if response.status_code in [400, 404]:
                    self.log_test(f"Req5 - Invalid ID {i+1}", True, 
                                f"Correctly handled invalid ID: {invalid_id}")
                else:
                    self.log_test(f"Req5 - Invalid ID {i+1}", False, 
                                f"Unexpected response for invalid ID {invalid_id}: {response.status_code}")
            except Exception as e:
                self.log_test(f"Req5 - Invalid ID {i+1}", True, 
                            f"Request properly failed for invalid ID: {invalid_id}")
        
        # Test 2: Verify error handling for malformed requests
        try:
            # Try to delete with malformed URL
            response = self.session.delete(f"{BASE_URL}/production/")
            if response.status_code in [400, 404, 405]:
                self.log_test("Req5 - Malformed URL", True, "Correctly handled malformed URL")
            else:
                self.log_test("Req5 - Malformed URL", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("Req5 - Malformed URL", True, "Request properly failed for malformed URL")
        
        # Test 3: Test concurrent deletion scenario (simulate)
        # Create a production first
        production_data = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 10
        }
        
        response = self.session.post(f"{BASE_URL}/production", json=production_data)
        if response.status_code == 200:
            production = response.json()
            production_id = production.get('id')
            
            # Delete it once
            response1 = self.session.delete(f"{BASE_URL}/production/{production_id}")
            # Try to delete it again (simulating concurrent deletion)
            response2 = self.session.delete(f"{BASE_URL}/production/{production_id}")
            
            if response1.status_code == 200 and response2.status_code == 404:
                self.log_test("Req5 - Concurrent Deletion", True, 
                            "Correctly handled concurrent deletion attempt")
            else:
                self.log_test("Req5 - Concurrent Deletion", False, 
                            f"Concurrent deletion handling error. First: {response1.status_code}, Second: {response2.status_code}")
        else:
            self.log_test("Req5 - Concurrent Deletion Setup", False, "Could not create production for concurrent test")
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Production Deletion Testing")
        print("Testing all requirements from the review request")
        print("=" * 70)
        
        # Test API connection
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print("❌ API connection failed. Stopping tests.")
                return
        except Exception as e:
            print(f"❌ API connection failed: {str(e)}. Stopping tests.")
            return
        
        try:
            # Run all requirement tests
            self.test_requirement_1_basic_deletion()
            self.test_requirement_2_nonexistent_production()
            self.test_requirement_3_fifo_restoration()
            self.test_requirement_4_business_logic()
            self.test_requirement_5_edge_cases()
            
        finally:
            # Cleanup
            self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by requirement
        print("\n📋 RESULTS BY REQUIREMENT:")
        requirements = {
            "Req1": "Basic Production Deletion",
            "Req2": "Delete Non-existent Production", 
            "Req3": "FIFO Material Restoration",
            "Req4": "Business Logic Verification",
            "Req5": "Edge Cases and Error Handling"
        }
        
        for req_key, req_name in requirements.items():
            req_tests = [r for r in self.test_results if r['test'].startswith(req_key)]
            req_passed = sum(1 for r in req_tests if r['success'])
            req_total = len(req_tests)
            status = "✅" if req_passed == req_total else "❌"
            print(f"  {status} {req_name}: {req_passed}/{req_total} passed")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = ComprehensiveProductionDeletionTester()
    results = tester.run_all_tests()