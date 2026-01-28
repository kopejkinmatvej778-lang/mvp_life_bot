from sqlalchemy import BigInteger, String, Integer, Float, DateTime, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    
    # Profile
    gender = Column(String, nullable=True) # 'male', 'female'
    age = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    goal = Column(String, nullable=True) # 'lose', 'maintain', 'gain'
    sport = Column(String, nullable=True) # 'home', 'gym', 'street'
    
    # Economics & Stats
    balance = Column(Integer, default=0)
    daily_calorie_limit = Column(Integer, default=2500)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class FoodLog(Base):
    __tablename__ = 'food_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    
    food_name = Column(String)
    calories = Column(Integer)
    protein = Column(Integer, nullable=True)
    fat = Column(Integer, nullable=True)
    carbs = Column(Integer, nullable=True)
    
    photo_file_id = Column(String, nullable=True) # For telegram file id if needed
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    title = Column(String)
    is_completed = Column(Integer, default=0) # 0 or 1
    type = Column(String, default='mission') # 'mission' or 'ritual'
