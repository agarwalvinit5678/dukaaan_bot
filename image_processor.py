import os
from PIL import Image, ImageEnhance

def remove_background(input_path: str, output_path: str):
    """
    Rembg uses too much memory for the 512MB Render free tier, so we are bypassing it.
    Instead, we will just copy the original image to the output path so we can upload it directly,
    while Nano Banana generates a brand new lifestyle image!
    """
    img = Image.open(input_path)
    img.save(output_path)

def enhance_image(image_path: str):
    """
    Enhances the brightness and sharpness of the image.
    Overwrites the image at image_path.
    """
    img = Image.open(image_path)
    enhancer_contrast = ImageEnhance.Contrast(img)
    img = enhancer_contrast.enhance(1.1)
    enhancer_sharpness = ImageEnhance.Sharpness(img)
    img = enhancer_sharpness.enhance(1.2)
    img.save(image_path)

def process_product_image(input_path: str, output_path: str):
    """
    Orchestrates the image processing: bypass background removal, just enhance.
    """
    try:
        print(f"Processing image: {input_path}")
        remove_background(input_path, output_path)
        enhance_image(output_path)
        print(f"Successfully processed and saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def composite_lifestyle_image(transparent_image_path: str, output_path: str, product_title: str) -> bool:
    """Generates an AI background and saves it directly, bypassing compositing since rembg OOMs."""
    try:
        from ai_assistant import generate_lifestyle_background
        bg_bytes = generate_lifestyle_background(product_title, transparent_image_path)
        if not bg_bytes:
            print("Failed to generate background bytes.")
            return False
            
        with open(output_path, "wb") as f:
            f.write(bg_bytes)
            
        print(f"Successfully saved AI lifestyle image to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving lifestyle image: {e}")
        return False
