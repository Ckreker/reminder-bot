"""
Модуль планировщика напоминаний.
Проверяет БД каждые 30 секунд и отправляет уведомления.
"""

import logging
import asyncio
from datetime import datetime
from typing import Callable, Awaitable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import Database

logger = logging.getLogger(__name__)


class ReminderScheduler:
	"""Планировщик для отправки напоминаний в нужное время."""
	
	def __init__(self, db: Database, bot_callback: Callable[[int, str], Awaitable[None]]):
		self.db = db
		self.bot_callback = bot_callback
		self.scheduler = BackgroundScheduler()
		self.is_running = False
		self.loop = None
	
	def start(self, loop=None):
		"""Запуск планировщика (проверка каждые 30 секунд)."""
		if self.is_running:
			return
		
		self.loop = loop or asyncio.get_event_loop()
		
		# Добавляем задачу как синхронную обёртку
		self.scheduler.add_job(
			self._check_reminders_sync,
			trigger=IntervalTrigger(seconds=30),
			id="check_reminders",
			replace_existing=True
		)
		self.scheduler.start()
		self.is_running = True
		logger.info("Планировщик запущен (проверка каждые 30 секунд)")
	
	def _check_reminders_sync(self):
		"""Синхронная обёртка для асинхронной проверки."""
		if self.loop and self.loop.is_running():
			asyncio.run_coroutine_threadsafe(self._check_reminders(), self.loop)
		else:
			# Если цикла нет, создаём временный
			asyncio.run(self._check_reminders())
	
	async def _check_reminders(self):
		"""Проверить, какие напоминания пора отправлять."""
		try:
			now = datetime.now()
			pending = self.db.get_all_pending_reminders()
			
			logger.debug(f"Проверка напоминаний: {len(pending)} ожидают")
			
			for rem_id, user_id, text, remind_time_str in pending:
				remind_time = datetime.fromisoformat(remind_time_str)
				if remind_time <= now:
					message = f"🔔 НАПОМИНАНИЕ 🔔\n\n📝 {text}"
					await self.bot_callback(user_id, message)
					self.db.mark_as_sent(rem_id)
					logger.info(f"Отправлено напоминание {rem_id} пользователю {user_id}")
		except Exception as e:
			logger.error(f"Ошибка в планировщике: {e}")
	
	def stop(self):
		"""Остановить планировщик."""
		if self.scheduler.running:
			self.scheduler.shutdown()
			self.is_running = False
			logger.info("Планировщик остановлен")