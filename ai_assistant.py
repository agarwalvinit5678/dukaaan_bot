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
        Generate the following details based on the image:
        1. "title": A catchy, SEO-friendly Title (max 60 characters).
        2. "description": A highly detailed, comprehensive, and professional product description formatted in HTML. It should cover everything: an engaging introduction, a bulleted list of key features and specifications, materials used, potential use cases, and why the customer should buy it. Use HTML tags like <p>, <ul>, <li>, <strong>, etc. Make it long and thorough.
        3. "base_price": An integer representing the selling price (discounted price). If the seller provided a price, use it! If not, estimate it in INR.
        4. "original_price": An integer representing the MRP. Usually 20% to 30% higher than base_price.
        5. "sku": A random, logical string (e.g., FRM-BLK-CLG-09).
        6. "stock_quantity": An integer for inventory (default 10).
        7. "weight": An integer for weight in grams (estimate).
        8. "hsn_code": A relevant 4 to 8 digit HSN code string for the product (e.g., "9403" for furniture, "4202" for bags).
        9. "gst_rate": An integer for GST percentage (e.g., 5, 12, 18, 28).
        10. "tags": A list of relevant string tags (e.g., ["home decor", "wooden", "wall art"]).
        11. "gtin": A random 12-14 digit GTIN/UPC string (or null if not applicable).
        12. "google_product_category": A relevant string from Google's product taxonomy (e.g., "Home & Garden > Decor").
        13. "seo_title": An SEO-optimized Title Tag (max 60 chars).
        14. "seo_description": An SEO-optimized Meta Description Tag (max 160 chars).

        Format your response EXACTLY as a JSON object with these exact keys: "title", "description", "base_price", "original_price", "sku", "stock_quantity", "weight", "hsn_code", "gst_rate", "tags", "gtin", "google_product_category", "seo_title", "seo_description".
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

def generate_lifestyle_background(product_title: str, image_path: str = None, user_notes: str = "") -> bytes:
    """Uses Gemini 3.1 Flash Image (Nano Banana) to generate a lifestyle background, directly editing the original image if provided."""
    try:
        from google import genai
        from google.genai import types
        import mimetypes
        
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model = "gemini-3.1-flash-image"
        
        # Build the parts
        parts = []
        
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/jpeg"
            parts.append(types.Part.from_bytes(data=img_data, mime_type=mime_type))
            
            prompt = f"Take this product ({product_title}), remove its original background, and place it seamlessly into a beautiful, highly realistic lifestyle scene. "
            if user_notes:
                prompt += f"\nTHE USER REQUESTED THIS SPECIFIC SETTING/PROMPT: '{user_notes}'. Please strictly follow their request for the background setting. "
            else:
                prompt += "\nPlace it in a clean, professional, well-lit studio environment with soft complementary colors, depth of field, and elegant subtle shadows that make the product pop. "
                
            prompt += "\n\nCRITICAL INSTRUCTION: Do NOT alter, redraw, or modify the product itself in any way. Preserve the product's original shape, text, branding, proportions, and details exactly as shown in the reference image. Only generate the surrounding background."
            
            parts.append(types.Part.from_text(text=prompt))
            print(f"Using Nano Banana to EDIT the image natively. Custom notes: {user_notes}")
        else:
            prompt = f"Generate a beautiful, highly realistic lifestyle background scene that would fit a product called '{product_title}'. "
            if user_notes:
                prompt += f"\nTHE USER REQUESTED THIS SPECIFIC SETTING: '{user_notes}'. "
            else:
                prompt += "Use a clean, professional, well-lit studio environment with soft complementary colors and elegant subtle shadows. "
                
            parts.append(types.Part.from_text(text=prompt))
            print(f"Using Nano Banana to GENERATE a lifestyle image from scratch. Custom notes: {user_notes}")

        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        if not response.candidates:
            print("No candidates returned from Nano Banana.")
            return None
            
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
                
        print("No inline image data found in Nano Banana response.")
        return None
        
    except Exception as e:
        print(f"Error generating lifestyle background with Nano Banana: {e}")
        return None
