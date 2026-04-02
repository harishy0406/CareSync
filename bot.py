import logging
import os
import telebot
from telebot import types
import requests

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🤖 CareSync Bot started!")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN in environment variables.")
    exit(1)

# OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("Missing OPENROUTER_API_KEY in environment variables.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_data = {}


# OpenRouter API Call
def get_ai_response(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.7
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"OpenRouter API Error: {e}")
        return "❌ Sorry, there was an issue fetching the AI response."


# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'role_selection'}
    welcome = f"""
👋 *Hello {message.from_user.first_name}!*  
🏥 *Welcome to CareSync Bot!*

I’m your smart medical assistant for health insights and support.

Please select your role:

*1* - 👨‍⚕️ Doctor  
*2* - 🧑‍🤝‍🧑 Patient
"""
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')


# Main Handler
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    if user_id not in user_data:
        user_data[user_id] = {'state': 'role_selection'}
    state = user_data[user_id]['state']
    
    # Universal Back Navigation
    if text == '0':
        if state.startswith('doctor'):
            user_data[user_id]['state'] = 'doctor_menu'
            show_doctor_menu(message)
        elif state.startswith('patient'):
            user_data[user_id]['state'] = 'patient_menu'
            show_patient_menu(message)
        else:
            user_data[user_id]['state'] = 'role_selection'
            start_command(message)
        return
    
    if state == 'role_selection':
        if text == '1':
            user_data[user_id]['state'] = 'doctor_menu'
            show_doctor_menu(message)
        elif text == '2':
            user_data[user_id]['state'] = 'patient_menu'
            show_patient_menu(message)
        else:
            bot.send_message(
                message.chat.id,
                "❓ Please type *1* for Doctor or *2* for Patient:",
                parse_mode='Markdown')

    elif state == 'doctor_menu':
        if text == '1':
            bot.send_message(
                message.chat.id,
                "📝 Please enter the following details:\n\n- Symptoms\n- Age\n- Medical history\n- Current medications",
                parse_mode='Markdown')
            user_data[user_id]['state'] = 'doctor_symptoms'
        elif text == '2':
            bot.send_message(
                message.chat.id,
                "💊 Enter drugs (separated by commas) to check interactions:",
                parse_mode='Markdown')
            user_data[user_id]['state'] = 'doctor_drugs'
        elif text == '3':
            bot.send_message(message.chat.id,
                             "🔬 Enter a condition to get diagnostic steps:",
                             parse_mode='Markdown')
            user_data[user_id]['state'] = 'doctor_diagnosis'
        elif text == '0':
            user_data[user_id]['state'] = 'role_selection'
            start_command(message)

    elif state == 'doctor_symptoms':
        prompt = f"Patient presents with:\n\n- Symptoms: {text}\n\nProvide: \n- Probable diagnosis\n- Recommended tests\n- Medication suggestions (if any) in short and simple bullet points use emojis"
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"🩺 *AI Diagnosis Suggestion:*\n\n{response}\n\n↩️ Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    elif state == 'doctor_drugs':
        prompt = f"Check for interactions or warnings for these drugs: {text}. Return short summary in short and simple bullet points use emojis."
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"💊 *Drug Interaction Report:*\n\n{response}\n\n↩️ Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    elif state == 'doctor_diagnosis':
        prompt = f"Provide structured diagnostic steps for the condition: {text}.in short and simple bullet points use emojis"
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"🔬 *Diagnostic Guidance:*\n\n{response}\n\n↩️ Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    elif state == 'patient_menu':
        if text == '4':
            bot.send_message(
                message.chat.id,
                "🩺 Please describe your issue (symptoms, duration):")
            user_data[user_id]['state'] = 'patient_specialist'
        elif text == '5':
            bot.send_message(
                message.chat.id,
                "📅 Enter details: Name, Date(dd-mm), Time(e.g. 4PM), Specialist"
            )
            user_data[user_id]['state'] = 'patient_appointment'
        elif text == '6':
            bot.send_message(
                message.chat.id,
                "💊 Enter your disease to get prescription advice:")
            user_data[user_id]['state'] = 'patient_prescription'
        elif text == '0':
            user_data[user_id]['state'] = 'role_selection'
            start_command(message)

    elif state == 'patient_specialist':
        prompt = f"Suggest the most suitable medical specialist for this case:\n\n{text}in short and simple bullet points use emojis"
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"👩‍⚕️ *Specialist Recommendation:*\n\n{response}\n\n↩️ Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'

    elif state == 'patient_prescription':
        prompt = f"Provide a short prescription guideline for: {text}. Mention dosage and precautions.in short and simple bullet points use emojis"
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"💊 *Prescription Info:*\n\n{response}\n\n↩️ Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'

    elif state == 'patient_appointment':
        try:
            name, date, time, specialist = map(str.strip, text.split(','))
            confirmation = f"""
✅ *Appointment Confirmed!*

👤 *Patient:* {name}  
📅 *Date:* {date}  
⏰ *Time:* {time}  
👨‍⚕️ *Doctor:* {specialist}

🔔 Please arrive 10 minutes early.
↩️ Press *0* to go back.
"""
            bot.send_message(message.chat.id,
                             "🔄 Booking appointment...",
                             parse_mode='Markdown')
            bot.send_message(message.chat.id,
                             confirmation,
                             parse_mode='Markdown')
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ Invalid format. Use: Name, Date, Time, Specialist",
                parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'

    elif text == '0':
        user_data[user_id]['state'] = 'role_selection'
        start_command(message)


# Menus
def show_doctor_menu(message):
    menu = """
👨‍⚕️ *Doctor Dashboard*

*1* - 🩺 Analyze Patient Symptoms  
*2* - 💊 Drug Interaction Check  
*3* - 🔬 Diagnostic Help  
*0* - 🔙 Main Menu
"""
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')


def show_patient_menu(message):
    menu = """
🧑‍🤝‍🧑 *Patient Dashboard*

*4* - 🏥 Get Specialist Suggestion  
*5* - 📅 Book Appointment  
*6* - 💊 Prescription Info  
*0* - 🔙 Main Menu
"""
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')


# Start Bot
if __name__ == '__main__':
    logger.info("🤖 CareSync Bot is running on Replit!")
    bot.infinity_polling()
