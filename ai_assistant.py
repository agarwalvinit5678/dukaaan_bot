import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_product_details(image_path: str, user_notes: str = None) -> dict:
    """Uses Gemini REST API to generate a rich product payload based on the image and user notes."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        return {"title": "Generated Product", "description": "Please update the description manually. AI generation failed."}
        
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
        prompt = """
        You are an expert e-commerce copywriter and product manager.
        I am providing an image of a product. Please analyze it and generate a rich product listing.
        """
        
        if user_notes:
            prompt += f"\nTHE SELLER ALSO PROVIDED THESE NOTES: \"{user_notes}\". Incorporate these notes heavily into your generation, especially extracting any price, material, or specific details mentioned!\n"
            
        prompt += """
        Generate the following details:
        1. "title": A catchy, SEO-friendly Title (max 60 characters).
        2. "description": A compelling Description detailing features, potential uses, and appeal.
        3. "base_price": An integer representing the selling price. If the seller provided a price in the notes, use it! If you cannot determine a price, return null.
        4. "original_price": An integer representing the MRP. If base_price is set, make this about 20% to 30% higher to show a discount. If no base_price, return null.
        5. "sku": A random, logical string (e.g., MAT-BLU-01) based on the item.
        6. "stock_quantity": An integer for inventory (default to 10 if not in notes).
        7. "weight": An integer for weight in grams (estimate, default 500).

        Format your response EXACTLY as a JSON object with these exact keys: "title", "description", "base_price", "original_price", "sku", "stock_quantity", "weight".
        Do not include any markdown formatting like ```json. Just raw JSON.
        """
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        result_text = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Clean up possible markdown code blocks from the response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return json.loads(result_text.strip())
        
    except Exception as e:
        print(f"Error generating details with Gemini REST API: {e}")
        try:
            print(f"API Response: {response.text}")
        except:
            pass
        return {"title": "Generated Product", "description": "Please update the description manually. AI generation failed."}

def generate_lifestyle_background(product_title: str) -> bytes:
    """Uses Gemini Imagen 4.0 to generate a lifestyle background based on the product title."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. Ask Gemini Text to generate a great prompt
    text_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    text_payload = {
        "contents": [{
            "parts": [{"text": f"Write a single sentence (max 20 words) describing a beautiful, modern, highly realistic lifestyle background scene that would fit a product called '{product_title}'. For example: 'A sleek modern wooden desk next to a bright window with a small coffee plant'. Do not mention the product itself, just the empty background scene."}]
        }]
    }
    
    prompt = "A beautiful modern wooden coffee table in a sunlit living room, depth of field, 4k"
    try:
        r = requests.post(text_url, json=text_payload, headers={'Content-Type': 'application/json'})
        if r.status_code == 200:
            prompt = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"Failed to generate dynamic prompt, falling back: {e}")
        
    print(f"Imagen Prompt: {prompt}")
    
    # 2. Call Imagen 4.0 API
    imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"
    imagen_payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1}
    }
    
    try:
        r = requests.post(imagen_url, json=imagen_payload, headers={'Content-Type': 'application/json'})
        r.raise_for_status()
        data = r.json()
        
        # The API returns predictions[0]['bytesBase64Encoded']
        b64_image = data['predictions'][0]['bytesBase64Encoded']
        return base64.b64decode(b64_image)
    except Exception as e:
        print(f"Error generating lifestyle background: {e}")
        try:
            print(r.text)
        except:
            pass
        return None
