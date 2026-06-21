import os
import requests
from dotenv import load_dotenv

load_dotenv()

DUKAAN_API_TOKEN = os.getenv("DUKAAN_API_TOKEN")
DUKAAN_STORE_UUID = os.getenv("DUKAAN_STORE_UUID")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

def upload_to_imgbb(image_path: str) -> str:
    """
    Uploads an image to ImgBB and returns the public URL.
    This is often required because Dukaan API might expect a URL rather than binary data.
    """
    if not IMGBB_API_KEY:
        raise ValueError("IMGBB_API_KEY is not set.")
    
    url = "https://api.imgbb.com/1/upload"
    
    with open(image_path, "rb") as file:
        payload = {
            "key": IMGBB_API_KEY,
        }
        files = {
            "image": file
        }
        response = requests.post(url, data=payload, files=files)
        
    if response.status_code == 200:
        data = response.json()
        return data["data"]["url"]
    else:
        raise Exception(f"Failed to upload to ImgBB: {response.text}")

def create_dukaan_product(details: dict, image_urls: list) -> dict:
    """
    Creates a product listing on the Dukaan store with rich fields using the v2 endpoint.
    Expects a list of image URLs.
    """
    if not DUKAAN_API_TOKEN or not DUKAAN_STORE_UUID:
        raise ValueError("Dukaan credentials are not set.")

    url = f"https://api.mydukaan.io/api/product/seller/{DUKAAN_STORE_UUID}/product/v2/"
    
    headers = {
        "Authorization": f"Bearer {DUKAAN_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    title = details.get("title", "New Product")
    desc = details.get("description", "")
    price = details.get("base_price", 0)
    orig_price = details.get("original_price", price)
    sku = details.get("sku", "")
    inv = details.get("stock_quantity", 10)
    
    primary_url = image_urls[0] if image_urls else ""
    
    # Exact payload structure expected by Dukaan API v2
    payload = {
        "name": title,
        "all_images": image_urls,
        "selling_price": price,
        "original_price": orig_price,
        "unit": "piece",
        "base_qty": 1,
        "description": f"<p>{desc}</p>",
        "categories": [13000145],  # Required Category ID
        "store": DUKAAN_STORE_UUID,
        "sku_code": sku,
        "skus": [
            {
                "sku_code": sku,
                "unit": "piece",
                "inventory": inv,
                "selling_price": price,
                "original_price": orig_price,
                "primary_image": primary_url,
                "all_images": image_urls,
                "attributes": [],
                "staffs": [],
                "metafields": [],
                "warehouse_inventory_items": [],
                "in_stock": True
            }
        ],
        "hsn_code": None,
        "gst_rate": 0,
        "weight_unit": "kg",
        "product_attributes": [],
        "staffs": [],
        "language_data": [],
        "is_taxable": False,
        "seo_data": {
            "title": title[:60],
            "description": desc[:160],
            "image": primary_url
        },
        "inventory_quantity": inv,
        "in_stock": True,
        "add_ons": []
    }
    
    if details.get("weight") is not None:
        payload["weight"] = details["weight"] / 1000.0  # Convert grams to kg
        payload["skus"][0]["volumetric_weight"] = payload["weight"]
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201, 202]:
        return response.json()
    else:
        raise Exception(f"Failed to create product on Dukaan: {response.status_code} - {response.text}")

def process_and_list_product(image_paths: list, details: dict):
    """
    High-level function to upload multiple images and list product with rich details.
    """
    print(f"Uploading {len(image_paths)} images to ImgBB...")
    public_urls = []
    for path in image_paths:
        url = upload_to_imgbb(path)
        public_urls.append(url)
        print(f"Image uploaded successfully: {url}")
        
    print("Creating product on Dukaan...")
    result = create_dukaan_product(details, public_urls)
    print("Product created successfully!")
    return result
