import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from flask import Flask
import threading
import os

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

# Setup dummy Flask server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am your Dukaan Store Assistant. 🛍️\n"
        "Send me a product picture, and I'll automatically enhance it, generate a description, and list it for you!"
    )
    return ConversationHandler.END

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles incoming photos."""
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

    # 3. Generate Details
    await update.message.reply_text("🧠 Analyzing the image to write a catchy title and description...")
    details = generate_product_details(processed_path)
    
    title = details.get("title", "Unknown")
    description = details.get("description", "No description")
    
    # Store these in the context so we can use them after getting the price
    context.user_data['draft_title'] = title
    context.user_data['draft_description'] = description
    context.user_data['processed_path'] = processed_path
    
    message = (
        f"**Generated Draft:**\n\n"
        f"**Title:** {title}\n"
        f"**Description:** {description}\n\n"
        f"💰 Please reply with the **Price** in rupees (just the number) to list this on Dukaan, or type 'cancel' to abort."
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    return WAITING_FOR_PRICE

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the price input and creates the listing."""
    text = update.message.text.strip()
    
    if text.lower() == 'cancel':
        await update.message.reply_text("❌ Listing cancelled. Send me another photo when you're ready!")
        # Clean up data
        context.user_data.clear()
        return ConversationHandler.END
        
    try:
        price = float(text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the price, or 'cancel'.")
        return WAITING_FOR_PRICE
        
    await update.message.reply_text(f"✅ Price set to ₹{price}. Uploading to Dukaan...")
    
    title = context.user_data.get('draft_title')
    description = context.user_data.get('draft_description')
    processed_path = context.user_data.get('processed_path')
    
    try:
        process_and_list_product(processed_path, title, description, price)
        await update.message.reply_text("🎉 **Successfully listed on your Dukaan store!**", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to list the product on Dukaan. Error: {e}")
        
    # Clean up data
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

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Set up the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            WAITING_FOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
