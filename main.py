from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from decouple import config
from firebase_config import db
import logging

# Enable logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
AGE, GENDER, GOAL = range(3)

# Start command
async def start(update: Update, context):
    await update.message.reply_text("Welcome! Let's get started. What's your age?")
    return AGE

# Get age
async def get_age(update: Update, context):
    try:
        age = int(update.message.text)
        context.user_data['age'] = age
        await update.message.reply_text("Great! What's your gender? (male/female/other)")
        return GENDER
    except ValueError:
        await update.message.reply_text("Please enter a valid number for age.")
        return AGE

# Get gender
async def get_gender(update: Update, context):
    gender = update.message.text.lower()
    if gender not in ['male', 'female', 'other']:
        await update.message.reply_text("Please choose from: male, female, or other.")
        return GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("What's your fitness goal? (lose_weight/gain_muscle/stay_fit)")
    return GOAL

# Save user data to Firestore
async def save_user_data(update: Update, context):
    goal = update.message.text.lower()
    if goal not in ['lose_weight', 'gain_muscle', 'stay_fit']:
        await update.message.reply_text("Invalid goal. Choose: lose_weight, gain_muscle, or stay_fit.")
        return GOAL
    
    user_id = str(update.message.from_user.id)
    user_data = {
        'age': context.user_data['age'],
        'gender': context.user_data['gender'],
        'goal': goal,
        'timestamp': db.SERVER_TIMESTAMP
    }
    db.collection('users').document(user_id).set(user_data)
    await update.message.reply_text("Profile saved! Use /workout for your plan.")
    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context):
    await update.message.reply_text("Onboarding canceled.")
    return ConversationHandler.END

def main():
    # Initialize bot
    bot_token = config("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(bot_token).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_user_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()