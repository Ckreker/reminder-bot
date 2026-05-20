"""
Модуль работы с базой данных SQLite.
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple


class Database:
	"""Класс для взаимодействия с БД напоминаний."""
	
	def __init__(self, db_path: str = "reminders.db"):
		self.db_path = db_path
		self.conn = sqlite3.connect(db_path, check_same_thread=False)
		self.cursor = self.conn.cursor()
		self._create_table()
	
	def _create_table(self):
		"""Создание таблицы reminders."""
		self.cursor.execute("""
			CREATE TABLE IF NOT EXISTS reminders (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				text TEXT NOT NULL,
				remind_time TEXT NOT NULL,
				created_at TEXT DEFAULT CURRENT_TIMESTAMP,
				is_sent INTEGER DEFAULT 0
			)
		""")
		self.conn.commit()
	
	def add_reminder(self, user_id: int, text: str, remind_time: datetime) -> int:
		"""Добавить новое напоминание. Возвращает ID."""
		self.cursor.execute(
			"INSERT INTO reminders (user_id, text, remind_time) VALUES (?, ?, ?)",
			(user_id, text, remind_time.isoformat())
		)
		self.conn.commit()
		return self.cursor.lastrowid
	
	def get_active_reminders(self, user_id: int) -> List[Tuple]:
		"""Получить все активные напоминания пользователя."""
		self.cursor.execute(
			"SELECT id, text, remind_time FROM reminders WHERE user_id = ? AND is_sent = 0 ORDER BY remind_time",
			(user_id,)
		)
		return self.cursor.fetchall()
	
	def get_all_pending_reminders(self) -> List[Tuple]:
		"""Получить все неотправленные напоминания."""
		self.cursor.execute(
			"SELECT id, user_id, text, remind_time FROM reminders WHERE is_sent = 0"
		)
		return self.cursor.fetchall()
	
	def mark_as_sent(self, reminder_id: int):
		"""Отметить напоминание как отправленное."""
		self.cursor.execute(
			"UPDATE reminders SET is_sent = 1 WHERE id = ?",
			(reminder_id,)
		)
		self.conn.commit()
	
	def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
		"""Удалить напоминание по ID."""
		self.cursor.execute(
			"DELETE FROM reminders WHERE id = ? AND user_id = ?",
			(reminder_id, user_id)
		)
		self.conn.commit()
		return self.cursor.rowcount > 0
	
	def get_reminder_count(self, user_id: int) -> int:
		"""Получить количество активных напоминаний."""
		self.cursor.execute(
			"SELECT COUNT(*) FROM reminders WHERE user_id = ? AND is_sent = 0",
			(user_id,)
		)
		return self.cursor.fetchone()[0]
	
	def close(self):
		"""Закрыть соединение с БД."""
		self.conn.close()