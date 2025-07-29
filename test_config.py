import os
import json

# Print all environment variables
print("=== All Environment Variables ===")
for k, v in sorted(os.environ.items()):
    if any(x in k.upper() for x in ['CORS', 'DOCC', 'API', 'LOG']):
        print(f"{k} = {repr(v)}")

print("\n=== Testing JSON parsing ===")
# Test what happens with empty string
test_value = os.environ.get('CORS_ORIGINS', '')
print(f"CORS_ORIGINS value: {repr(test_value)}")
print(f"Is it empty string? {test_value == ''}")
print(f"Length: {len(test_value)}")

if test_value:
    try:
        result = json.loads(test_value)
        print(f"JSON parse successful: {result}")
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")

print("\n=== Testing Pydantic Settings ===")
try:
    from backend.core.config import Settings
    settings = Settings()
    print("Settings loaded successfully!")
    print(f"CORS origins: {settings.docc_cors_origins}")
except Exception as e:
    print(f"Failed to load settings: {e}")
    import traceback
    traceback.print_exc()