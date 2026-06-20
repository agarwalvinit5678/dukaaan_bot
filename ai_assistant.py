import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def generate_product_details(image_path: str) -> dict:
    """
    Sends the image to Google Gemini to generate a product title and description.
    Returns a dictionary with 'title' and 'description' keys.
    """
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")

    # We use gemini-1.5-flash as it is fast and supports multimodal input (images + text)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Upload the file to Gemini's File API (temporary storage for processing)
    # Alternatively, we can pass the image data directly if it's small, but File API is safer.
    # Let's pass the PIL image directly.
    import PIL.Image
    img = PIL.Image.open(image_path)
    
    prompt = (
        "You are an expert e-commerce copywriter. Look at this product image and generate "
        "a catchy title and a detailed, persuasive description for an online store listing.\n"
        "Return the response ONLY as a valid JSON object with two keys: 'title' and 'description'.\n"
        "Do not include any markdown formatting like ```json, just the raw JSON object."
    )
    
    try:
        response = model.generate_content([prompt, img])
        response_text = response.text.strip()
        
        # Clean up any potential markdown formatting the model might still include
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        data = json.loads(response_text)
        
        return {
            "title": data.get("title", "Unknown Product"),
            "description": data.get("description", "No description available.")
        }
    except Exception as e:
        print(f"Error generating details with Gemini: {e}")
        return {
            "title": "Generated Product",
            "description": "Please update the description manually. AI generation failed."
        }
