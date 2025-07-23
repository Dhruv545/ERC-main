#!/usr/bin/env python3
"""
Diagnostic test to understand the production and heat management issues
"""

import requests
import json
from datetime import date, datetime
import time

BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

def diagnostic_test():
    session = requests.Session()
    
    print("🔍 DIAGNOSTIC TEST - Understanding Production and Heat Issues")
    print("=" * 60)
    
    # Step 1: Create a fresh heat
    print("\n1. Creating a fresh heat...")
    heat_data = {
        "heat_number": f"DIAG_{int(time.time())}",
        "steel_type": "20.64mm",
        "quantity_kg": 500.0,
        "date_received": date.today().isoformat()
    }
    
    response = session.post(f"{BASE_URL}/heat", json=heat_data)
    if response.status_code == 200:
        heat = response.json()
        print(f"✅ Heat created: {heat.get('heat_number')}")
        print(f"   ID: {heat.get('id')}")
        print(f"   Original quantity: {heat.get('quantity_kg')}kg")
        print(f"   Remaining quantity: {heat.get('remaining_kg')}kg")
        heat_id = heat.get('id')
    else:
        print(f"❌ Failed to create heat: {response.status_code} - {response.text}")
        return
    
    # Step 2: Check all heats before production
    print("\n2. Checking all heats before production...")
    response = session.get(f"{BASE_URL}/heats")
    if response.status_code == 200:
        all_heats = response.json()
        print(f"Total heats in system: {len(all_heats)}")
        for h in all_heats:
            if h.get('steel_type') == '20.64mm':
                print(f"   Heat {h.get('heat_number')}: {h.get('remaining_kg')}kg remaining (original: {h.get('quantity_kg')}kg)")
    
    # Step 3: Record production
    print("\n3. Recording production...")
    production_data = {
        "date": date.today().isoformat(),
        "product_type": "MK-III",
        "quantity_produced": 50  # Should consume 46.5kg
    }
    
    response = session.post(f"{BASE_URL}/production", json=production_data)
    if response.status_code == 200:
        production = response.json()
        print(f"✅ Production recorded: {production.get('id')}")
        print(f"   Product type: {production.get('product_type')}")
        print(f"   Quantity produced: {production.get('quantity_produced')}")
        print(f"   Material consumed: {production.get('material_consumed_kg')}kg")
        production_id = production.get('id')
    else:
        print(f"❌ Failed to record production: {response.status_code} - {response.text}")
        return
    
    # Step 4: Check heats after production
    print("\n4. Checking heats after production...")
    response = session.get(f"{BASE_URL}/heats")
    if response.status_code == 200:
        all_heats_after = response.json()
        for h in all_heats_after:
            if h.get('steel_type') == '20.64mm':
                print(f"   Heat {h.get('heat_number')}: {h.get('remaining_kg')}kg remaining (original: {h.get('quantity_kg')}kg)")
                if h.get('id') == heat_id:
                    print(f"   ^^^ Our test heat - should have consumed 46.5kg")
    
    # Step 5: Check inventory status
    print("\n5. Checking inventory status...")
    response = session.get(f"{BASE_URL}/inventory")
    if response.status_code == 200:
        inventory = response.json()
        for item in inventory:
            if item.get('steel_type') == '20.64mm':
                print(f"   20.64mm Steel:")
                print(f"     Total received: {item.get('total_received_kg')}kg")
                print(f"     Total consumed: {item.get('total_consumed_kg')}kg")
                print(f"     Current stock: {item.get('current_stock_kg')}kg")
    
    # Step 6: Try to delete the production
    print("\n6. Deleting production...")
    response = session.delete(f"{BASE_URL}/production/{production_id}")
    if response.status_code == 200:
        deletion_result = response.json()
        print(f"✅ Production deleted successfully")
        print(f"   Material restored: {deletion_result.get('material_restored_kg')}kg")
        print(f"   Remaining unrestored: {deletion_result.get('remaining_unrestored_kg')}kg")
    else:
        print(f"❌ Failed to delete production: {response.status_code} - {response.text}")
    
    # Step 7: Check heats after deletion
    print("\n7. Checking heats after deletion...")
    response = session.get(f"{BASE_URL}/heats")
    if response.status_code == 200:
        all_heats_final = response.json()
        for h in all_heats_final:
            if h.get('steel_type') == '20.64mm':
                print(f"   Heat {h.get('heat_number')}: {h.get('remaining_kg')}kg remaining (original: {h.get('quantity_kg')}kg)")
                if h.get('id') == heat_id:
                    print(f"   ^^^ Our test heat - should be back to 500kg")
    
    # Step 8: Try to delete the heat
    print("\n8. Trying to delete the heat...")
    response = session.delete(f"{BASE_URL}/heat/{heat_id}")
    if response.status_code == 200:
        print(f"✅ Heat deleted successfully")
    elif response.status_code == 400:
        print(f"✅ Heat deletion correctly prevented: {response.json().get('detail', 'No details')}")
    else:
        print(f"❌ Unexpected response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    diagnostic_test()