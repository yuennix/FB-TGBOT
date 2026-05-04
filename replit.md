# FB-TGBOT

## Overview
A Telegram bot that automates Facebook account creation and management. Built with Python using the aiogram library for Telegram bot functionality.

## Architecture
- **bot.py** - Telegram bot entry point using aiogram v3. Handles commands, user approval flow, credits system, and account creation workflows.
- **main.py** - Facebook automation library. Contains account creation logic, name pools, session handling, and web scraping utilities.

## Key Features
- Facebook account creation automation
- Telegram bot interface for user interaction
- Owner approval system for new users
- Credit-based usage system
- GitHub-based user data persistence (users.json on `data` branch)
- Support for Filipino and RPW name pools

## Configuration
The bot requires the following environment variables (set as Replit Secrets):
- `BOT_TOKEN` - Telegram Bot API token (from @BotFather)
- `OWNER_ID` - Telegram user ID of the bot owner
- `GITHUB_TOKEN` - GitHub personal access token for user data storage

## Running
The bot runs as a background console process:
```
python3 bot.py
```

## Dependencies
- `aiogram>=3.0.0` - Telegram bot framework
- `requests>=2.31.0` - HTTP requests
- `faker>=20.0.0` - Fake data generation
- `fake-useragent>=1.4.0` - Random user agents
- `beautifulsoup4>=4.12.0` - HTML parsing
- `rich>=13.0.0` - Console output formatting
- `python-dotenv>=1.0.0` - Environment variable loading
- `certifi>=2024.2.2` - SSL certificates
