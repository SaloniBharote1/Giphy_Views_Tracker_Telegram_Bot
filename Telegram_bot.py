import requests
import telebot
from bs4 import BeautifulSoup
import schedule
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import threading

telegram_Token = "Telegram_token_id"
Giphy_API_Key = "giphy_api_key"

bot = telebot.TeleBot(telegram_Token)
tracked_projects = {}  # Storing locally for now we can also used database for storing

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the Daily Giphy Views Tracker Bot! Please enter the Giphy project ID which you want to track!")

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "Commands:\n Use /start - for Start the bot\n Use /help - Get help\n Use /track And then Mention <project_id> - to Track a Giphy project\n Use /daily_updates - For Enable daily updates\n Use /stop_updates - For Stop daily updates")

@bot.message_handler(commands=['daily_updates'])
def enable_daily_updates(message):
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = True
    bot.reply_to(message, "Daily updates enabled for tracked projects.")

@bot.message_handler(commands=['stop_updates'])
def stop_daily_updates(message):
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = False

def send_daily_updates():
    print('UPDATES')
    for project_id, project_info in tracked_projects.items():
        if project_info and project_info['message'] and project_info['daily_updates_enabled']:
            fetch_project_views(project_info['message'])

schedule.every().day.at("12:00").do(send_daily_updates)

def telegram_polling():
    bot.infinity_polling()

def job():
    print("Bot is working Now...")
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['track'])
def fetch_project_views(message):
    try:
        if len(message.text.split()) >= 2:
            print(message.chat.first_name)
            project_id = message.text.split(' ', 1)[1]
            tracked_projects[project_id] = {"message": message, 'chat_id': message.chat.id, 'daily_updates_enabled': False}
            bot.reply_to(message, f"Project {project_id} is now being tracked. Please wait for view count.")
            url = f"https://giphy.com/gifs/{project_id}"
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--headless=new')
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            driver.implicitly_wait(10)
            html = driver.page_source
            driver.close()
            soup = BeautifulSoup(html, 'html.parser')
            views_element = soup.find('div', class_='ViewCountContainer-sc-15ri43l')
            if views_element:
                views = views_element.text
                bot.reply_to(message, f"Total views for project {project_id}: {views}")
            else:
                bot.reply_to(message, f"Views data not found for project {project_id}")
        else:
            bot.reply_to(message, "Please specify the project ID after the /views command.")
    except requests.RequestException as e:
        print(f"Error fetching views for project {project_id}: {e}")
        bot.reply_to(message, f"Error fetching views for project {project_id}: {e}")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"An unexpected error occurred: {e}")

thread1 = threading.Thread(target=telegram_polling)
thread1.start()
thread2 = threading.Thread(target=job)
thread2.start()
