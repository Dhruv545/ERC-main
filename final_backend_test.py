#!/usr/bin/env python3
"""
Final comprehensive backend test with unique identifiers
"""

import requests
import json
from datetime import date, datetime
import time
import uuid

BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

def run_final_tests():
    """Run final comprehensive tests"""
    print("🚀 Final Backend API Testing")
    print("=" * 50)
    
    # Generate unique identifiers
    timestamp = int(time.time())
    unique_heat_1 = f"H{timestamp}001"
    unique_heat_2 = f"H{timestamp}002"
    unique_heat_test = f"H{timestamp}TEST"
    
    results = []
    
    # Test 1: Add unique heat records
    print("\n1. Testing Heat Management...")
    
    heat_data_1 = {
        "heat_number": unique_heat_1,
        "steel_type": "20.64mm",
        "quantity_kg": 300.0,
        "date_received": date.today().isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/heat", json=heat_data_1)
    if response.status_code == 200:
        print("✅ Add 20.64mm heat: SUCCESS")
        results.append(("Add 20.64mm heat", True))
    else:
        print(f"❌ Add 20.64mm heat: FAILED ({response.status_code})")
        results.append(("Add 20.64mm heat", False))
    
    heat_data_2 = {
        "heat_number": unique_heat_2,
        "steel_type": "23mm",
        "quantity_kg": 400.0,
        "date_received": date.today().isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/heat", json=heat_data_2)
    if response.status_code == 200:
        print("✅ Add 23mm heat: SUCCESS")
        results.append(("Add 23mm heat", True))
    else:
        print(f"❌ Add 23mm heat: FAILED ({response.status_code})")
        results.append(("Add 23mm heat", False))
    
    # Test 2: Test duplicate validation
    response = requests.post(f"{BASE_URL}/heat", json=heat_data_1)
    if response.status_code == 400:
        print("✅ Duplicate validation: SUCCESS")
        results.append(("Duplicate validation", True))
    else:
        print(f"❌ Duplicate validation: FAILED ({response.status_code})")
        results.append(("Duplicate validation", False))
    
    # Test 3: Production with material consumption
    print("\n2. Testing Production Management...")
    
    production_data = {
        "date": date.today().isoformat(),
        "product_type": "MK-III",
        "quantity_produced": 50
    }
    
    response = requests.post(f"{BASE_URL}/production", json=production_data)
    if response.status_code == 200:
        prod_result = response.json()
        consumed = prod_result.get('material_consumed_kg')
        expected = 50 * 0.930
        if abs(consumed - expected) < 0.01:
            print(f"✅ MK-III production: SUCCESS (consumed {consumed}kg)")
            results.append(("MK-III production", True))
        else:
            print(f"❌ MK-III production: Material calculation error")
            results.append(("MK-III production", False))
    else:
        print(f"❌ MK-III production: FAILED ({response.status_code})")
        results.append(("MK-III production", False))
    
    # Test 4: Inventory status
    print("\n3. Testing Inventory Status...")
    
    response = requests.get(f"{BASE_URL}/inventory")
    if response.status_code == 200:
        inventory = response.json()
        steel_types = [item.get('steel_type') for item in inventory]
        if "20.64mm" in steel_types and "23mm" in steel_types:
            print("✅ Inventory status: SUCCESS")
            results.append(("Inventory status", True))
            
            # Check stock calculations
            for item in inventory:
                steel_type = item.get('steel_type')
                total_received = item.get('total_received_kg', 0)
                total_consumed = item.get('total_consumed_kg', 0)
                current_stock = item.get('current_stock_kg', 0)
                
                expected_stock = total_received - total_consumed
                if abs(current_stock - expected_stock) < 0.01:
                    print(f"✅ Stock calculation {steel_type}: SUCCESS")
                    results.append((f"Stock calculation {steel_type}", True))
                else:
                    print(f"❌ Stock calculation {steel_type}: FAILED")
                    results.append((f"Stock calculation {steel_type}", False))
        else:
            print("❌ Inventory status: Missing steel types")
            results.append(("Inventory status", False))
    else:
        print(f"❌ Inventory status: FAILED ({response.status_code})")
        results.append(("Inventory status", False))
    
    # Test 5: Dashboard data
    print("\n4. Testing Dashboard Data...")
    
    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        required_fields = ['inventory_status', 'recent_productions', 'recent_heats', 
                         'total_production_mkiii', 'total_production_mkv']
        
        missing_fields = [field for field in required_fields if field not in dashboard]
        if not missing_fields:
            print("✅ Dashboard data: SUCCESS")
            results.append(("Dashboard data", True))
        else:
            print(f"❌ Dashboard data: Missing fields {missing_fields}")
            results.append(("Dashboard data", False))
    else:
        print(f"❌ Dashboard data: FAILED ({response.status_code})")
        results.append(("Dashboard data", False))
    
    # Test 6: FIFO workflow test
    print("\n5. Testing FIFO Workflow...")
    
    # Get initial inventory
    response = requests.get(f"{BASE_URL}/inventory")
    if response.status_code == 200:
        initial_inventory = response.json()
        initial_stock_20_64 = next((item['current_stock_kg'] for item in initial_inventory 
                                  if item['steel_type'] == '20.64mm'), 0)
        
        # Record production
        test_production = {
            "date": date.today().isoformat(),
            "product_type": "MK-III",
            "quantity_produced": 20  # Should consume 18.6kg
        }
        
        response = requests.post(f"{BASE_URL}/production", json=test_production)
        if response.status_code == 200:
            # Check final inventory
            response = requests.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                final_inventory = response.json()
                final_stock_20_64 = next((item['current_stock_kg'] for item in final_inventory 
                                        if item['steel_type'] == '20.64mm'), 0)
                
                expected_reduction = 20 * 0.930  # 18.6kg
                actual_reduction = initial_stock_20_64 - final_stock_20_64
                
                if abs(actual_reduction - expected_reduction) < 0.01:
                    print("✅ FIFO workflow: SUCCESS")
                    results.append(("FIFO workflow", True))
                else:
                    print(f"❌ FIFO workflow: Stock reduction error")
                    results.append(("FIFO workflow", False))
            else:
                print("❌ FIFO workflow: Failed to get final inventory")
                results.append(("FIFO workflow", False))
        else:
            print(f"❌ FIFO workflow: Production failed ({response.status_code})")
            results.append(("FIFO workflow", False))
    else:
        print("❌ FIFO workflow: Failed to get initial inventory")
        results.append(("FIFO workflow", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n🔍 FAILED TESTS:")
        for test_name, success in results:
            if not success:
                print(f"  ❌ {test_name}")
    
    return results

if __name__ == "__main__":
    run_final_tests()