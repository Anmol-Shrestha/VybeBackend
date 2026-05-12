"""
Validates the structure and content of users.json and restaurants.json
"""
import json
from pathlib import Path

def validate_users_data():
    """Validate users.json structure"""
    filepath = Path(__file__).parent.parent / "test" / "users.json"

    try:
        with open(filepath) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ users.json not found at {filepath}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in users.json: {e}")
        return False

    print("\n📋 Validating users.json...")

    if not isinstance(data, dict):
        print("⚠️  Expected single user object, found:", type(data).__name__)
        return False

    required_fields = {"name", "userID", "dietary", "allergen"}
    missing = required_fields - set(data.keys())
    if missing:
        print(f"❌ Missing required fields: {missing}")
        print(f"   Found fields: {set(data.keys())}")
        return False

    print(f"✅ User: {data['name']} (ID: {data['userID']})")
    print(f"   Dietary: {data['dietary']}")
    print(f"   Allergens: {data['allergen']}")

    return True


def validate_restaurants_data():
    """Validate restaurants.json structure"""
    filepath = Path(__file__).parent.parent / "test" / "restaurants.json"

    try:
        with open(filepath) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ restaurants.json not found at {filepath}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in restaurants.json: {e}")
        return False

    print("\n📋 Validating restaurants.json...")

    if not isinstance(data, list):
        print(f"❌ Expected array of restaurants, found: {type(data).__name__}")
        return False

    print(f"✅ Found {len(data)} restaurants\n")

    required_fields = {
        "name", "address_display", "latitude", "longitude",
        "cuisine", "dietary", "meal_types","price_max",
        "has_parking", "has_live_music", "max_capacity", "service_hours", "ai_metadata"
    }

    issues = []

    for i, restaurant in enumerate(data, 1):
        missing = required_fields - set(restaurant.keys())
        if missing:
            issues.append(f"   [{i}] {restaurant.get('name', 'Unknown')}: Missing {missing}")

        # Validate location
        if not isinstance(restaurant.get('latitude'), (int, float)):
            issues.append(f"   [{i}] {restaurant.get('name')}: Invalid latitude")
        if not isinstance(restaurant.get('longitude'), (int, float)):
            issues.append(f"   [{i}] {restaurant.get('name')}: Invalid longitude")

        # Check dietary is a list
        if not isinstance(restaurant.get('dietary'), list):
            issues.append(f"   [{i}] {restaurant.get('name')}: 'dietary' should be list, got {type(restaurant.get('dietary')).__name__}")

        # Check service_hours format
        hours = restaurant.get('service_hours', {})
        has_string_format = any(isinstance(v, str) for v in hours.values())
        has_int_format = any(isinstance(v, dict) for v in hours.values())

        if has_string_format and has_int_format:
            issues.append(f"   [{i}] {restaurant.get('name')}: Mixed service_hours formats")

    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(issue)
        return False

    print("✅ All restaurants have required fields")
    for restaurant in data:
        print(f"   • {restaurant['name']} - {restaurant['address_display']}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    users_ok = validate_users_data()
    restaurants_ok = validate_restaurants_data()

    print("\n" + "=" * 60)
    if users_ok and restaurants_ok:
        print("✅ All validations passed!")
    else:
        print("❌ Validation failed - please review the issues above")
    print("=" * 60)