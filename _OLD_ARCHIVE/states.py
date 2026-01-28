from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_photo = State()

class FoodTrackingStates(StatesGroup):
    chatting = State()  # Режим чата про еду
    awaiting_food = State() # Ожидание фото или текста еды
