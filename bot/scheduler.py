"""
Модуль планировщика напоминаний.
"""

import logging
from datetime import datetime
from typing import Callable, Awaitable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import Database

logger = logging.getLogger(__name__)


class ReminderScheduler:
	"""Планировщик для отправки напоминаний."""
	
	def __init__(self, db: Database, bot_callback: Callable[[int, str], Awaitable[None]]):
		self.db = db
		self.bot_callback = bot_callback
		self.scheduler = BackgroundScheduler()
		self.is_running = False
	
	def start(self):
		"""Запуск планировщика (проверка каждые 30 секунд)."""
		if self.is_running:
			return
		
		self.scheduler.add_job(
			self._check_reminders,
			trigger=IntervalTrigger(seconds=30),
			id="check_reminders",
			replace_existing=True
		)
		self.scheduler.start()
		self.is_running = True
		logger.info("Планировщик запущен")
	
	async def _check_reminders(self):
		"""Проверить, какие напоминания пора отправлять."""
		try:
			now = datetime.now()
			pending = self.db.get_all_pending_reminders()
			
			for rem_id, user_id, text, remind_time_str in pending:
				remind_time = datetime.fromisoformat(remind_time_str)
				if remind_time <= now:
					message = f"🔔 НАПОМИНАНИЕ 🔔\n\n📝 {text}"
					await self.bot_callback(user_id, message)
					self.db.mark_as_sent(rem_id)
					logger.info(f"Отправлено напоминание {rem_id}")
		except Exception as e:
			logger.error(f"Ошибка в планировщике: {e}")
	
	def stop(self):
		"""Остановить планировщик."""
		if self.scheduler.running:
			self.scheduler.shutdown()
			self.is_running = False