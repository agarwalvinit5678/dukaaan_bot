import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
from io import BytesIO
from PIL import Image, ImageEnhance
from rembg import remove, new_session

def remove_background(input_path: str, output_path: str):
    """
    Removes the background from the image at input_path and saves it to output_path.
    """
    with open(input_path, 'rb') as i:
        input_data = i.read()
    
    # Use the 'u2netp' lightweight model instead of default 'u2net' to stay under 512MB RAM
    session = new_session("u2netp")
    # rembg requires image bytes and returns image bytes
    output_data = remove(input_data, session=session)
    
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

def composite_lifestyle_image(transparent_image_path: str, output_path: str, product_title: str) -> bool:
    """Generates an AI background and composites the transparent product onto it."""
    try:
        from ai_assistant import generate_lifestyle_background
        
        # 1. Generate background
        bg_bytes = generate_lifestyle_background(product_title)
        if not bg_bytes:
            print("Failed to generate background bytes.")
            return False
            
        # 2. Open images
        product_img = Image.open(transparent_image_path).convert("RGBA")
        bg_img = Image.open(BytesIO(bg_bytes)).convert("RGBA")
        
        # 3. Resize background to match product (or vice versa). Let's resize bg to product.
        # It's better to fit the product into the center of the background.
        # Resize product to 80% of background width
        target_width = int(bg_img.width * 0.8)
        aspect_ratio = product_img.height / product_img.width
        target_height = int(target_width * aspect_ratio)
        
        # Ensure we don't scale up the product beyond its original quality too much
        if target_width > product_img.width * 1.5:
            target_width = product_img.width
            target_height = product_img.height
            
        product_img_resized = product_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 4. Calculate center position
        x = (bg_img.width - target_width) // 2
        y = (bg_img.height - target_height) // 2
        
        # 5. Composite
        bg_img.paste(product_img_resized, (x, y), product_img_resized)
        
        # 6. Save as RGB (JPEG)
        final_img = bg_img.convert("RGB")
        final_img.save(output_path, "JPEG", quality=90)
        print(f"Successfully saved lifestyle image to {output_path}")
        return True
    except Exception as e:
        print(f"Error compositing lifestyle image: {e}")
        return False
