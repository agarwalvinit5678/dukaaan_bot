import os

# STRICT MEMORY LIMITS for ONNX/rembg on Render 512MB free tier
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from flask import Flask
import threading
import os

# Setup dummy Flask server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Import our custom modules
from image_processor import process_product_image
from ai_assistant import generate_product_details
from dukaan_client import process_and_list_product

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Define states for the conversation
WAITING_FOR_PRICE = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am your Dukaan Store Assistant. 🛍️\n"
        "Send me a product picture, optionally with notes in the caption (like price or materials), and I'll automatically generate a listing for you!"
    )
    return ConversationHandler.END

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles incoming photos and captions."""
    user_notes = update.message.caption or ""
    
    await update.message.reply_text("📸 Received your photo! Let me process it...")
    
    # 1. Download the photo
    photo_file = await update.message.photo[-1].get_file()
    
    # Create directories if they don't exist
    os.makedirs("input_images", exist_ok=True)
    os.makedirs("processed_images", exist_ok=True)
    
    input_path = f"input_images/{photo_file.file_id}.jpg"
    processed_path = f"processed_images/{photo_file.file_id}.png"
    
    await photo_file.download_to_drive(input_path)
    
    # 2. Enhance the image
    await update.message.reply_text("✨ Enhancing the image (removing background & improving lighting)...")
    success = process_product_image(input_path, processed_path)
    
    if not success:
        await update.message.reply_text("❌ Failed to process the image. Please try again with a different photo.")
        return ConversationHandler.END
        
    # Send the enhanced image back to the user to show the result
    await update.message.reply_photo(photo=open(processed_path, 'rb'), caption="Here is the enhanced version!")

    # 3. Generate Details using Image and Notes
    msg = "🧠 Analyzing the image"
    if user_notes:
        msg += " and your notes"
    await update.message.reply_text(msg + " to write a comprehensive listing...")
    
    details = generate_product_details(processed_path, user_notes=user_notes)
    
    title = details.get("title", "Unknown")
    description = details.get("description", "No description")
    base_price = details.get("base_price")
    
    # 3.5 Generate Lifestyle Image
    await update.message.reply_text("🎨 Asking Nano Banana to generate a beautiful lifestyle background...")
    lifestyle_path = f"processed_images/{photo_file.file_id}_lifestyle.jpg"
    from image_processor import composite_lifestyle_image
    
    image_paths = [processed_path]
    has_lifestyle = composite_lifestyle_image(processed_path, lifestyle_path, title, user_notes)
    
    if has_lifestyle:
        await update.message.reply_photo(photo=open(lifestyle_path, 'rb'), caption="Here is the Nano Banana lifestyle version!")
        image_paths.insert(0, lifestyle_path) # Put lifestyle image first (primary)
    
    # Check if AI found a valid base price
    if base_price is not None and isinstance(base_price, (int, float)) and base_price > 0:
        message = (
            f"**Generated Draft:**\n\n"
            f"**Title:** {title}\n"
            f"**Price:** ₹{base_price}\n"
            f"*(Extracted from your notes!)*\n\n"
            f"**Description:** {description}\n\n"
            f"Uploading directly to Dukaan..."
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        
        try:
            process_and_list_product(image_paths, details)
            await update.message.reply_text("🎉 **Successfully listed on your Dukaan store!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to list the product on Dukaan. Error: {e}")
            
        return ConversationHandler.END
        
    else:
        # Save details and ask for price manually
        context.user_data['draft_details'] = details
        context.user_data['image_paths'] = image_paths
        
        message = (
            f"**Generated Draft:**\n\n"
            f"**Title:** {title}\n"
            f"**Description:** {description}\n\n"
            f"💰 Please reply with the **Price** in rupees (just the number) to list this on Dukaan, or type 'cancel' to abort."
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return WAITING_FOR_PRICE

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles manual price input and creates the listing."""
    text = update.message.text.strip()
    
    if text.lower() == 'cancel':
        await update.message.reply_text("❌ Listing cancelled. Send me another photo when you're ready!")
        context.user_data.clear()
        return ConversationHandler.END
        
    try:
        price = float(text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the price, or 'cancel'.")
        return WAITING_FOR_PRICE
        
    await update.message.reply_text(f"✅ Price set to ₹{price}. Uploading to Dukaan...")
    
    details = context.user_data.get('draft_details', {})
    image_paths = context.user_data.get('image_paths')
    
    # Inject the manual price into the rich details payload
    details['base_price'] = price
    
    try:
        process_and_list_product(image_paths, details)
        await update.message.reply_text("🎉 **Successfully listed on your Dukaan store!**", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to list the product on Dukaan. Error: {e}")
        
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set. Please check your .env file.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            WAITING_FOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)



    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
