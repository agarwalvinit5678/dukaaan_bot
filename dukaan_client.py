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

def create_dukaan_product(title: str, description: str, price: float, image_url: str) -> dict:
    """
    Creates a product listing on the Dukaan store.
    """
    if not DUKAAN_API_TOKEN or not DUKAAN_STORE_UUID:
        raise ValueError("Dukaan credentials are not set.")

    # Dukaan's API endpoint structure usually looks like this.
    # Note: Depending on the exact API version, this endpoint might vary slightly.
    # Typically, it's https://mydukaan.io/api/v1/stores/{store_uuid}/products
    # We will use the standard v1 structure as a starting point.
    url = f"https://mydukaan.io/api/v1/stores/{DUKAAN_STORE_UUID}/products"
    
    headers = {
        "Authorization": f"Bearer {DUKAAN_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": title,
        "description": description,
        "price": price,
        # 'media' or 'images' array depending on the exact Dukaan spec
        "images": [
            {
                "url": image_url
            }
        ],
        "is_hidden": False,
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Failed to create product on Dukaan: {response.status_code} - {response.text}")

def process_and_list_product(image_path: str, title: str, description: str, price: float):
    """
    High-level function to upload image and list product.
    """
    print("Uploading image to ImgBB...")
    public_url = upload_to_imgbb(image_path)
    print(f"Image uploaded successfully: {public_url}")
    
    print("Creating product on Dukaan...")
    result = create_dukaan_product(title, description, price, public_url)
    print("Product created successfully!")
    return result
