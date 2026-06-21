import os
import json
import google.generativeai as genai
import PIL.Image

def get_gemini_model():
    """Initializes and returns the Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        return None
        
    try:
        genai.configure(api_key=api_key)
        # Use gemini-pro-vision instead of 1.5-flash to ensure compatibility with older google-generativeai package
        model = genai.GenerativeModel('gemini-pro-vision')
        return model
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None

def generate_product_details(image_path: str) -> dict:
    """Uses Gemini to generate a title and description based on the image."""
    model = get_gemini_model()
    if not model:
        return {"title": "Generated Product", "description": "Please update the description manually. AI generation failed."}
        
    try:
        img = PIL.Image.open(image_path)
        
        prompt = """
        You are an expert e-commerce copywriter.
        I am providing an image of a product. Please analyze it and generate:
        1. A catchy, SEO-friendly Title (max 60 characters).
        2. A compelling Description detailing its features, potential uses, and appeal.
        Format your response EXACTLY as a JSON object with two keys: "title" and "description".
        Do not include any markdown formatting like ```json. Just raw JSON.
        """
        
        response = model.generate_content([prompt, img])
        
        result_text = response.text.strip()
        
        # Clean up possible markdown code blocks from the response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return json.loads(result_text.strip())
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini JSON response: {e}\nRaw Response: {response.text}")
        return {"title": "New Product", "description": response.text}
    except Exception as e:
        print(f"Error generating details with Gemini: {e}")
        return {"title": "Generated Product", "description": "Please update the description manually. AI generation failed."}
