from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="reminder-bot",
    version="1.0.0",
    author="Your Team",
    description="Telegram bot for reminders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "python-telegram-bot>=20.0",
        "APScheduler>=3.10",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "reminder-bot=bot.main:main",
        ],
    },
)
