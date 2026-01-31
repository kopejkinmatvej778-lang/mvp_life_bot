from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_name"),
            InlineKeyboardButton(text="🖼 Изменить фото", callback_data="edit_photo")
        ]
    ]
)
