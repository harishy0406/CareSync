import logging
import os
import telebot
from telebot import types
import requests

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🤖 CareSync Bot started!")

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not TELEGRAM_BOT_TOKEN or not OPENROUTER_API_KEY:
    logger.error("Missing TELEGRAM_BOT_TOKEN or OPENROUTER_API_KEY")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_data = {}


# OpenRouter AI Call
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
        return "⚠️ Sorry, something went wrong with the AI response."


# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'role_selection'}
    welcome = f"""
🏥 *Welcome to CareSync Bot, {message.from_user.first_name}!*

I’m your smart assistant for medical guidance, appointments, and more.

Please select your role:

*1* - 👨‍⚕️ Doctor  
*2* - 🙋‍♂️ Patient
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

    # Role Selection
    if state == 'role_selection':
        if text == '1':
            user_data[user_id]['state'] = 'doctor_menu'
            show_doctor_menu(message)
        elif text == '2':
            user_data[user_id]['state'] = 'patient_menu'
            show_patient_menu(message)
        else:
            bot.send_message(message.chat.id,
                             "❗Please type *1* for Doctor or *2* for Patient.",
                             parse_mode='Markdown')

    # Doctor Dashboard
    elif state == 'doctor_menu':
        if text == '1':
            bot.send_message(message.chat.id,
                             "🩺 Please enter patient symptoms:")
            user_data[user_id]['state'] = 'doctor_symptoms'
        elif text == '2':
            bot.send_message(
                message.chat.id,
                "💊 Enter a drug or condition to check interactions:")
            user_data[user_id]['state'] = 'doctor_drugs'
        elif text == '3':
            bot.send_message(message.chat.id,
                             "🔬 Enter condition for diagnostic help:")
            user_data[user_id]['state'] = 'doctor_diagnosis'

    elif state == 'doctor_symptoms':
        prompt = f"""You're a medical AI. Based on the symptoms below, provide:
- 2 likely diagnoses
- Recommended medication
- Basic treatment plan

Symptoms: {text}
"""
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"🧠 *AI Analysis:*\n\n{response}\n\n🔁 Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    elif state == 'doctor_drugs':
        prompt = f"""Check for drug interactions and safety info:
- Name: {text}
- Use bullet points to explain effects, warnings, and interactions."""
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"💊 *Drug Info:*\n\n{response}\n\n🔁 Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    elif state == 'doctor_diagnosis':
        prompt = f"""Suggest diagnostic procedures for:
- Condition: {text}
- Provide steps and tests in bullet points."""
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"🔬 *Diagnostics Guide:*\n\n{response}\n\n🔁 Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'doctor_menu'

    # Patient Dashboard
    elif state == 'patient_menu':
        if text == '4':
            bot.send_message(message.chat.id,
                             "🏥 Please enter your symptoms or condition:")
            user_data[user_id]['state'] = 'patient_specialist'
        elif text == '5':
            bot.send_message(message.chat.id,
                             "📅 Enter: Name, Date(dd-mm), Time, Specialist")
            user_data[user_id]['state'] = 'patient_appointment'
        elif text == '6':
            bot.send_message(message.chat.id,
                             "💊 Enter your disease to get prescription tips:")
            user_data[user_id]['state'] = 'patient_prescription'

    elif state == 'patient_specialist':
        prompt = f"""You're a medical assistant. Based on this condition, suggest:
- Specialist type
- 1-2 alternative options

Condition: {text}"""
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"👨‍⚕️ *Recommended Specialist:*\n\n{response}\n\n🔁 Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'

    elif state == 'patient_prescription':
        prompt = f"""Suggest:
- Common prescription medicines
- Usage/dosage guidelines (general)
- Important precautions

For condition: {text}"""
        response = get_ai_response(prompt)
        bot.send_message(
            message.chat.id,
            f"💊 *Prescription Info:*\n\n{response}\n\n🔁 Press *0* to go back.",
            parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'

    elif state == 'patient_appointment':
        try:
            name, date, time, specialist = map(str.strip, text.split(','))
            confirmation = f"""
✅ *Appointment Booked!*

👤 *Name:* {name}  
📅 *Date:* {date}  
🕒 *Time:* {time}  
👨‍⚕️ *Doctor:* {specialist}

📌 Please arrive 10 mins early.  
🔁 Press *0* to go back.
"""
            bot.send_message(message.chat.id,
                             confirmation,
                             parse_mode='Markdown')
        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ Invalid format! Please use: Name, Date, Time, Specialist",
                parse_mode='Markdown')
        user_data[user_id]['state'] = 'patient_menu'


# Dashboards
def show_doctor_menu(message):
    menu = """
👨‍⚕️ *Doctor Dashboard*

*1* - 🩺 Analyze Symptoms  
*2* - 💊 Drug Interaction Check  
*3* - 🔬 Diagnostic Steps  
*0* - 🔙 Back
"""
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')


def show_patient_menu(message):
    menu = """
🙋‍♂️ *Patient Dashboard*

*4* - 🏥 Find Specialist  
*5* - 📅 Book Appointment  
*6* - 💊 Get Prescription Advice  
*0* - 🔙 Back
"""
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')


# Run Bot
if __name__ == '__main__':
    logger.info("🤖 CareSync Bot is running on Replit!")
    bot.infinity_polling()
