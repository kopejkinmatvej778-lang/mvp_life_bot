from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def get_main_keyboard():
    # LINK TO YOUR GITHUB PAGES FRONTEND
    WEB_APP_URL = "https://kopejkinmatvej778-lang.github.io/mvp_life_bot/web_app/index.html"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚡ ENTER MVP OS", web_app=WebAppInfo(url=WEB_APP_URL))],
            [KeyboardButton(text="👤 PROFILE"), KeyboardButton(text="💰 WALLET")]
        ],
        resize_keyboard=True
    )
