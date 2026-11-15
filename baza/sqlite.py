import sqlite3
import time

class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)

        if commit:
            connection.commit()
        if fetchall:
            data = cursor.fetchall()
        if fetchone:
            data = cursor.fetchone()
        connection.close()
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users(
            full_name TEXT,
            telegram_id NUMBER UNIQUE,
            language TEXT
        );
        """
        self.execute(sql, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([f"{item} = ?" for item in parameters])
        return sql, tuple(parameters.values())

    def add_user(self, telegram_id:int, full_name:str, language:str = "us"):
        sql = """
        INSERT INTO Users(telegram_id, full_name, language) VALUES(?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
        language=excluded.language;
        """
        self.execute(sql, parameters=(telegram_id, full_name, language), commit=True)

    def select_all_users(self):
        sql = "SELECT * FROM Users;"
        return self.execute(sql, fetchall=True)

    def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE"
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def update_user_language(self, telegram_id: int, language: str):
        sql = "UPDATE Users SET language = ? WHERE telegram_id = ?"
        self.execute(sql, parameters=(language, telegram_id), commit=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM Users;", fetchone=True)

    def select_user_by_id(self, telegram_id: int):
        sql = "SELECT * FROM Users WHERE telegram_id = ?"
        return self.execute(sql, parameters=(telegram_id,), fetchone=True)

    def delete_users(self):
        self.execute("DELETE FROM Users WHERE TRUE;", commit=True)

    def all_users_id(self):
        return self.execute("SELECT telegram_id FROM Users;", fetchall=True)

    def create_table_channels(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Channels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE
        );
        """
        self.execute(sql, commit=True)

    def add_channel(self, channel_id: str):
        sql = "INSERT OR IGNORE INTO Channels(channel_id) VALUES(?)"
        self.execute(sql, parameters=(channel_id,), commit=True)

    def delete_channel(self, channel_id: str):
        sql = "DELETE FROM Channels WHERE channel_id = ?"
        self.execute(sql, parameters=(channel_id,), commit=True)

    def get_channels(self):
        sql = "SELECT channel_id FROM Channels;"
        rows = self.execute(sql, fetchall=True)
        return [row[0] for row in rows] if rows else []

    def create_table_anon_tokens(self):
        """Anonim xabar tokenlari jadvali.

        TOKEN -> user_id jadvali: tokenning ichida hech qanday ID yo'q,
        kim ekanligini faqat shu baza biladi. Bot restart bo'lsa ham
        eski linklar ishlashda davom etadi.
        """
        sql = """
        CREATE TABLE IF NOT EXISTS AnonTokens(
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at REAL
        );
        """
        self.execute(sql, commit=True)

    def add_anon_token(self, token: str, user_id: int):
        sql = "INSERT OR REPLACE INTO AnonTokens(token, user_id, created_at) VALUES(?, ?, ?)"
        self.execute(sql, parameters=(token, user_id, time.time()), commit=True)

    def get_anon_user(self, token: str):
        sql = "SELECT user_id FROM AnonTokens WHERE token = ?"
        row = self.execute(sql, parameters=(token,), fetchone=True)
        return row[0] if row else None

    def create_table_stickers(self):
        """Foydalanuvchining shaxsiy stiker kolleksiyasi.

        Stikerni botga yuborsangiz - file_id bazaga saqlanadi, keyin
        bir bosishda istalgan chatga qayta yuborish mumkin.
        """
        sql = """
        CREATE TABLE IF NOT EXISTS Stickers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            file_id TEXT NOT NULL UNIQUE,
            title TEXT,
            created_at REAL
        );
        """
        self.execute(sql, commit=True)

    def add_sticker(self, owner_id: int, file_id: str, title: str):
        sql = "INSERT OR IGNORE INTO Stickers(owner_id, file_id, title, created_at) VALUES(?, ?, ?, ?)"
        self.execute(sql, parameters=(owner_id, file_id, title, time.time()), commit=True)

    def select_stickers(self, owner_id: int):
        sql = "SELECT id, file_id, title FROM Stickers WHERE owner_id = ? ORDER BY id DESC;"
        return self.execute(sql, parameters=(owner_id,), fetchall=True)

    def count_stickers(self, owner_id: int):
        sql = "SELECT COUNT(*) FROM Stickers WHERE owner_id = ?"
        return self.execute(sql, parameters=(owner_id,), fetchone=True)

    def delete_sticker(self, owner_id: int, sticker_row_id: int):
        sql = "DELETE FROM Stickers WHERE owner_id = ? AND id = ?"
        self.execute(sql, parameters=(owner_id, sticker_row_id), commit=True)

    def search_stickers(self, owner_id: int, query: str):
        sql = "SELECT id, file_id, title FROM Stickers WHERE owner_id = ? AND title LIKE ? ORDER BY id DESC LIMIT 20"
        return self.execute(sql, parameters=(owner_id, f"%{query}%"), fetchall=True)

    # ---------------- Admin boshqaradigan stiker paketlari ----------------

    def create_table_sticker_packs(self):
        """Admin yaratadigan stiker paketlari va ularning stikerlari."""
        sql = """
        CREATE TABLE IF NOT EXISTS StickerPacks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_by INTEGER,
            created_at REAL
        );
        """
        self.execute(sql, commit=True)
        sql2 = """
        CREATE TABLE IF NOT EXISTS PackStickers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            title TEXT,
            FOREIGN KEY(pack_id) REFERENCES StickerPacks(id)
        );
        """
        self.execute(sql2, commit=True)

    def add_sticker_pack(self, title: str, created_by: int):
        sql = "INSERT INTO StickerPacks(title, created_by, created_at) VALUES(?, ?, ?)"
        self.execute(sql, parameters=(title, created_by, time.time()), commit=True)

    def get_sticker_packs(self):
        sql = """
        SELECT p.id, p.title, COUNT(s.id) FROM StickerPacks p
        LEFT JOIN PackStickers s ON s.pack_id = p.id
        GROUP BY p.id ORDER BY p.id;
        """
        return self.execute(sql, fetchall=True)

    def delete_sticker_pack(self, pack_id: int):
        self.execute("DELETE FROM PackStickers WHERE pack_id = ?", parameters=(pack_id,), commit=True)
        self.execute("DELETE FROM StickerPacks WHERE id = ?", parameters=(pack_id,), commit=True)

    def add_pack_sticker(self, pack_id: int, file_id: str, title: str):
        sql = "INSERT INTO PackStickers(pack_id, file_id, title) VALUES(?, ?, ?)"
        self.execute(sql, parameters=(pack_id, file_id, title), commit=True)

    def get_pack_stickers(self, pack_id: int):
        sql = "SELECT id, file_id, title FROM PackStickers WHERE pack_id = ? ORDER BY id;"
        return self.execute(sql, parameters=(pack_id,), fetchall=True)

    def delete_pack_sticker(self, sticker_row_id: int):
        self.execute("DELETE FROM PackStickers WHERE id = ?", parameters=(sticker_row_id,), commit=True)

    def get_pack_sticker_file(self, sticker_row_id: int):
        sql = "SELECT pack_id, file_id, title FROM PackStickers WHERE id = ?"
        return self.execute(sql, parameters=(sticker_row_id,), fetchone=True)

    def count_pack_stickers(self, pack_id: int):
        sql = "SELECT COUNT(*) FROM PackStickers WHERE pack_id = ?"
        return self.execute(sql, parameters=(pack_id,), fetchone=True)

    # ---------------- Umumiy stikerlar kolleksiyasi (faqat admin qo'shadi) ----------------

    def create_table_shared_stickers(self):
        """Admin to'plagan umumiy stikerlar - barcha foydalanuvchilar ko'radi/ishlatadi."""
        sql = """
        CREATE TABLE IF NOT EXISTS SharedStickers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            title TEXT,
            added_by INTEGER,
            added_at REAL
        );
        """
        self.execute(sql, commit=True)

    def add_shared_sticker(self, file_id: str, title: str, added_by: int):
        sql = "INSERT INTO SharedStickers(file_id, title, added_by, added_at) VALUES(?, ?, ?, ?)"
        self.execute(sql, parameters=(file_id, title, added_by, time.time()), commit=True)

    def get_shared_stickers(self):
        sql = "SELECT id, file_id, title FROM SharedStickers ORDER BY id DESC;"
        return self.execute(sql, fetchall=True)

    def count_shared_stickers(self):
        row = self.execute("SELECT COUNT(*) FROM SharedStickers", fetchone=True)
        return row[0] if row else 0

    def delete_shared_sticker(self, row_id: int):
        self.execute("DELETE FROM SharedStickers WHERE id = ?", parameters=(row_id,), commit=True)

    def get_shared_sticker_file(self, row_id: int):
        sql = "SELECT id, file_id, title FROM SharedStickers WHERE id = ?"
        return self.execute(sql, parameters=(row_id,), fetchone=True)

    def search_shared_stickers(self, query: str):
        sql = "SELECT id, file_id, title FROM SharedStickers WHERE title LIKE ? ORDER BY id DESC LIMIT 20"
        return self.execute(sql, parameters=(f"%{query}%",), fetchall=True)

# Create database instance
db = Database()
