from config import Config
import sqlite3
import json
from datetime import datetime
import os


class Database:
    def __init__(self):
        self.db_path = 'db/cards_destiny.db'
        if not os.path.exists('db'):
            os.makedirs('db')
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Пользователи
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,  -- Telegram User ID
                username TEXT,
                full_name TEXT,
                birth_date TEXT,
                registration_date TEXT DEFAULT CURRENT_TIMESTAMP,
                is_premium INTEGER DEFAULT 0,  -- Boolean: 0 или 1
                premium_until TEXT,
                settings TEXT,  -- JSON строка
                last_activity TEXT,
                last_name TEXT,  -- Добавленное поле для сохранения последнего использованного имени
                last_birth_date TEXT  -- Добавленное поле для сохранения последней даты рождения
            )''')

        # Подписки
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_type TEXT CHECK(subscription_type IN ('monthly', 'yearly')),
                start_date TEXT,
                end_date TEXT,
                payment_id TEXT,
                amount REAL,
                status TEXT CHECK(status IN ('active', 'expired', 'cancelled')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

        # Рефералы
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                referral_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT CHECK(status IN ('pending', 'completed')),
                reward_claimed INTEGER DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referred_id) REFERENCES users (id)
            )''')

        # Уведомления
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                notification_type TEXT CHECK(
                    notification_type IN ('daily', 'period_start', 'premium_expiration', 'referral_update')
                ),
                scheduled_time TEXT,
                status TEXT CHECK(status IN ('pending', 'sent', 'failed')),
                content TEXT,  -- JSON строка
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

        # История раскладов
        c.execute('''CREATE TABLE IF NOT EXISTS spreads_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                spread_type TEXT CHECK(spread_type IN ('daily', 'period', 'year')),
                spread_data TEXT,  -- JSON строка
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

        # Расшаренные расклады
        c.execute('''CREATE TABLE IF NOT EXISTS shared_spreads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_uuid TEXT UNIQUE,
                user_id INTEGER,
                spread_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (spread_id) REFERENCES spreads_history (id)
            )''')

        # Создаём индексы для оптимизации
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_schedule ON notifications(scheduled_time)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shared_spreads_uuid ON shared_spreads(share_uuid)')

        conn.commit()
        conn.close()

    def get_user(self, user_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return c.fetchone()

    def add_user(self, user_id, username, full_name, birth_date):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO users (id, username, full_name, birth_date, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, full_name, birth_date, datetime.now().isoformat()))
            conn.commit()
            return c.lastrowid

    def save_user_data(self, user_id, name=None, birth_date=None):
        with self.get_connection() as conn:
            c = conn.cursor()

            # Сначала проверяем существование пользователя
            c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not c.fetchone():
                # Если пользователь не существует, создаем его
                c.execute('''
                    INSERT INTO users (id, last_name, last_birth_date)
                    VALUES (?, ?, ?)
                ''', (user_id, name, birth_date))
            else:
                # Если пользователь существует, обновляем данные
                update_fields = []
                params = []

                if name is not None:
                    update_fields.append("last_name = ?")
                    params.append(name)

                if birth_date is not None:
                    update_fields.append("last_birth_date = ?")
                    params.append(birth_date)

                if update_fields:
                    params.append(user_id)
                    query = f'''
                        UPDATE users 
                        SET {", ".join(update_fields)}
                        WHERE id = ?
                    '''
                    c.execute(query, params)

            conn.commit()

    def get_user_data(self, user_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT last_name, last_birth_date 
                FROM users 
                WHERE id = ?
            ''', (user_id,))
            result = c.fetchone()
            if result:
                return {
                    'name': result[0],
                    'birth_date': result[1]
                }
            return None

    def update_user_activity(self, user_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE users 
                SET last_activity = ? 
                WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            conn.commit()

    def save_spread(self, user_id, spread_type, data):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO spreads_history (user_id, spread_type, spread_data)
                VALUES (?, ?, ?)
            ''', (user_id, spread_type, json.dumps(data)))
            conn.commit()
            return c.lastrowid

    def add_referral(self, referrer_id, referred_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO referrals (referrer_id, referred_id, status)
                VALUES (?, ?, 'pending')
            ''', (referrer_id, referred_id))
            conn.commit()

            # Проверяем количество рефералов
            c.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_id = ? AND status = 'completed'
            ''', (referrer_id,))
            count = c.fetchone()[0]

            return count

    def update_premium_status(self, user_id, is_premium, premium_until):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE users 
                SET is_premium = ?, premium_until = ?
                WHERE id = ?
            ''', (1 if is_premium else 0, premium_until, user_id))
            conn.commit()