#!/usr/bin/env python3
"""
Focused test for remaining issues
"""

import requests
import json
from datetime import date

BASE_URL = "https://b36f873b-5f1f-4d88-8761-a6aca06d52b5.preview.emergentagent.com/api"

def test_duplicate_heat():
    """Test duplicate heat validation"""
    heat_data = {
        "heat_number": "H2024001",
        "steel_type": "20.64mm",
        "quantity_kg": 500.0,
        "date_received": date.today().isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/heat", json=heat_data)
    print(f"Duplicate heat test: Status {response.status_code}, Response: {response.text}")

def test_invalid_data():
    """Test invalid data handling"""
    invalid_heat = {
        "heat_number": "",
        "steel_type": "invalid_type",
        "quantity_kg": -100
    }
    
    response = requests.post(f"{BASE_URL}/heat", json=invalid_heat)
    print(f"Invalid data test: Status {response.status_code}, Response: {response.text}")

def test_insufficient_stock():
    """Test insufficient stock scenario"""
    large_production = {
        "date": date.today().isoformat(),
        "product_type": "MK-III",
        "quantity_produced": 100000  # This should exceed available stock
    }
    
    response = requests.post(f"{BASE_URL}/production", json=large_production)
    print(f"Insufficient stock test: Status {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    test_duplicate_heat()
    test_invalid_data()
    test_insufficient_stock()