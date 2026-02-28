#!/usr/bin/env python3
"""
Example script demonstrating how to use the Temperature Measurements Service
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def health_check():
    """Check if the service is running"""
    print("\n--- Health Check ---")
    response = requests.get(f"{BASE_URL}/")
    print(json.dumps(response.json(), indent=2))


def submit_measurements():
    """Submit sample temperature measurements"""
    print("\n--- Submitting Measurements ---")
    
    measurements = {
        "measurements": [
            {
                "sensorAddress": "sensor-001",
                "temperature": 22.5,
                "timestamp": datetime.now().isoformat()
            },
            {
                "sensorAddress": "sensor-002",
                "temperature": 18.3,
                "timestamp": (datetime.now() - timedelta(minutes=1)).isoformat()
            },
            {
                "sensorAddress": "sensor-001",
                "temperature": 23.1,
                "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat()
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/measurements",
        json=measurements,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def get_all_measurements():
    """Get all stored measurements"""
    print("\n--- Getting All Measurements ---")
    response = requests.get(f"{BASE_URL}/api/measurements")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def get_sensor_measurements(sensor_address):
    """Get measurements for a specific sensor"""
    print(f"\n--- Getting Measurements for {sensor_address} ---")
    response = requests.get(f"{BASE_URL}/api/measurements/{sensor_address}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def clear_measurements():
    """Clear all measurements"""
    print("\n--- Clearing All Measurements ---")
    response = requests.delete(f"{BASE_URL}/api/measurements")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    try:
        # Run examples
        health_check()
        submit_measurements()
        get_all_measurements()
        get_sensor_measurements("sensor-001")
        get_sensor_measurements("sensor-002")
        clear_measurements()
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the service.")
        print("Make sure the service is running with:")
        print("  python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")
