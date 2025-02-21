import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'db', 'cards_destiny.db')
    EXCEL_PATH = os.path.join(BASE_DIR, 'matrix.xlsx')
    SECRET_KEY = 'your-secret-key-here'  # Для JWT токенов
    DEBUG = True