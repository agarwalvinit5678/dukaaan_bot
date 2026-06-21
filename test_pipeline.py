import os
import sys
from image_processor import process_product_image
from ai_assistant import generate_product_details
from dukaan_client import process_and_list_product

if len(sys.argv) < 2:
    print("Usage: python test_pipeline.py <image_path>")
    sys.exit(1)

input_path = sys.argv[1]
processed_path = "processed_test_image.png"

print("1. Enhancing image (removing background & improving lighting)...")
success = process_product_image(input_path, processed_path)
if not success:
    print("Image processing failed.")
    sys.exit(1)

print("\n2. Sending enhanced image to Gemini API...")
# Adding mock user_notes to test the new extraction logic
user_notes = "Handmade beaded table mat, price is 299 rs."
details = generate_product_details(processed_path, user_notes=user_notes)

print("\n--- GENERATED DRAFT ---")
print(f"Title: {details.get('title')}")
print(f"Price: {details.get('base_price')}")
print(f"Original Price: {details.get('original_price')}")
print(f"SKU: {details.get('sku')}")
print(f"Inventory: {details.get('stock_quantity')}")
print(f"Weight: {details.get('weight')}")
print(f"Description: {details.get('description')}")
print("-----------------------")

print("\n3. Testing End-to-End Upload to Dukaan API...")
try:
    result = process_and_list_product(processed_path, details)
    print("\n✅ Dukaan API Success!")
    print(result)
except Exception as e:
    print("\n❌ Dukaan API Failed!")
    print(str(e))
