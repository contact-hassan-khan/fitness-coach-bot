from telegram import Update
from firebase_admin import firestore
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
        'timestamp': firestore.SERVER_TIMESTAMP
    }
    db.collection('users').document(user_id).set(user_data)
    await update.message.reply_text("Profile saved! Use /workout for your plan.")
    return ConversationHandler.END


# Workout command
async def workout(update: Update, context):
    user_id = str(update.message.from_user.id)
    user_doc = db.collection('users').document(user_id).get()

    if not user_doc.exists:
        await update.message.reply_text("Please complete onboarding with /start first.")
        return

    user_data = user_doc.to_dict()
    goal = user_data.get('goal')
    
    if not goal:
        await update.message.reply_text("No fitness goal set. Please complete onboarding. /start")
        return

    # Generate workout based on goal
    if goal == 'lose_weight':
        plan = """
        *Weight Loss Workout*  
        - 30 min brisk walk/jog  
        - 3 sets of 15 squats  
        - 3 sets of 10 push-ups (knees optional)  
        - 3 sets of 20 jumping jacks  
        - [Video Demo](https://youtu.be/example)
        """
    elif goal == 'gain_muscle':
        plan = """
        *Muscle Building Workout*  
        - 5 sets of 8 barbell squats  
        - 4 sets of 10 bench presses  
        - 4 sets of 12 pull-ups  
        - 3 sets of 15 deadlifts  
        - [Video Demo](https://youtu.be/example)
        """
    else:
        plan = """
        *Maintenance Workout*  
        - 20 min yoga/stretching  
        - 3 sets of 12 lunges  
        - 3 sets of 15 planks (30 sec hold)  
        - 2 sets of 20 mountain climbers  
        - [Video Demo](https://youtu.be/example)
        """

    await update.message.reply_text(plan, parse_mode='Markdown')
# Log workout command
async def log_workout(update: Update, context):
    user_id = str(update.message.from_user.id)
    user_doc = db.collection('users').document(user_id).get()

    if not user_doc.exists:
        await update.message.reply_text("Please complete onboarding with /start first.")
        return

    # Log workout to Firestore
    log_entry = {
        'timestamp': db.SERVER_TIMESTAMP,
        'workout': ' '.join(context.args) if context.args else 'No details provided'
    }
    db.collection('users').document(user_id).collection('workout_logs').add(log_entry)
    await update.message.reply_text("Workout logged successfully!")

# Stats command
async def stats(update: Update, context):
    user_id = str(update.message.from_user.id)
    logs = db.collection('users').document(user_id).collection('workout_logs').stream()

    total_workouts = sum(1 for _ in logs)
    await update.message.reply_text(f"You've logged *{total_workouts} workouts*!", parse_mode='Markdown')
    
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
    
    application.add_handler(CommandHandler('workout', workout)) # Workout command
    application.add_handler(CommandHandler('log', log_workout)) # Log workout command
    application.add_handler(CommandHandler('stats', stats)) # Stats command
    application.add_handler(conv_handler)
    application.run_polling()
    

if __name__ == "__main__":
    main()