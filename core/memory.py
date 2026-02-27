import sqlite3
from pathlib import Path

class MemoryManager:
    """Quản lý lịch sử hội thoại của người dùng bằng SQLite."""
    
    def __init__(self, db_path="storage/memory.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        """
        Thêm một tin nhắn vào lịch sử.
        :param session_id: ID của user hoặc group chat.
        :param role: "user" hoặc "model" (Gemini format).
        :param content: Nội dung tin nhắn.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (session_id, role, content)
                VALUES (?, ?, ?)
            ''', (str(session_id), role, content))
            conn.commit()

    def get_chat_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """
        Lấy N tin nhắn gần nhất của một session.
        :return: Danh sách dict [{'role': 'user', 'content': '...'}, ...]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Lấy N tin nhắn mới nhất
            cursor.execute('''
                SELECT role, content FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (str(session_id), limit))
            rows = cursor.fetchall()
            
            # Phải đảo ngược để trở thành (cũ nhất -> mới nhất) giống lịch sử chat thực tế
            history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
            return history

    def clear_history(self, session_id: str):
        """Xóa lịch sử của một session (phục vụ nếu user gõ /reset)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (str(session_id),))
            conn.commit()

# Khởi tạo instance mặc định (Singleton-ish) cho cả app
memory = MemoryManager()
