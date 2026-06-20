import os
from io import BytesIO
from PIL import Image, ImageEnhance
from rembg import remove

def remove_background(input_path: str, output_path: str):
    """
    Removes the background from the image at input_path and saves it to output_path.
    """
    with open(input_path, 'rb') as i:
        input_data = i.read()
    
    # rembg requires image bytes and returns image bytes
    output_data = remove(input_data)
    
    with open(output_path, 'wb') as o:
        o.write(output_data)

def enhance_image(image_path: str):
    """
    Enhances the brightness and sharpness of the image.
    Overwrites the image at image_path.
    """
    # Open the image
    img = Image.open(image_path)
    
    # Increase contrast
    enhancer_contrast = ImageEnhance.Contrast(img)
    img = enhancer_contrast.enhance(1.1)  # 10% increase
    
    # Increase sharpness
    enhancer_sharpness = ImageEnhance.Sharpness(img)
    img = enhancer_sharpness.enhance(1.2) # 20% increase
    
    # Save it back
    img.save(image_path)

def process_product_image(input_path: str, output_path: str):
    """
    Orchestrates the image processing: background removal followed by enhancement.
    """
    try:
        print(f"Processing image: {input_path}")
        # Remove background and save to output_path
        remove_background(input_path, output_path)
        
        # Enhance the resulting image
        enhance_image(output_path)
        print(f"Successfully processed and saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False
