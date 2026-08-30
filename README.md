<p align="center">
  <img src="https://graph.org/file/7e859b8397fafe899bc7f-c0f3be688b6551f8c9.jpg" width="100%" alt="Bot Banner">
</p>

<p align="center">
  <a href="https://github.com">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=32&pause=1000&color=F75C7E&center=true&vCenter=true&width=500&lines=%F0%9F%8E%AC+Movie+Filter+Bot" alt="Typing SVG" />
  </a>
</p>

<p align="center">
  A Telegram bot that auto-searches and delivers movies/series from your connected channels — with premium subscriptions, force-subscribe, referral rewards, and more.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Framework-Pyrogram-orange">
  <img src="https://img.shields.io/badge/Database-MongoDB-green?logo=mongodb&logoColor=white">
  <img src="https://img.shields.io/badge/Deploy-Koyeb-purple">
</p>

---

## ✨ Features

- 🔍 **Auto-Filter Search** — finds and sends matching movies/series automatically when someone types a name in a connected group
- 🎬 **IMDB Integration** — shows poster, rating, cast, and other details with search results
- 💎 **Premium System** — subscription plans via UPI or Telegram Stars, with expiry tracking (`/plan`, `/myplan`)
- 🔒 **Premium-Locked Movies** — mark specific movies as premium-only (`/lockmovie`, `/unlockmovie`, `/lockedlist`) with a public "🎬 Premium Movies" button so users can see what's exclusive
- 🎥 **Paid Streaming Links** — non-premium users are prompted to upgrade before generating a stream link
- 🤑 **Earn Money (Referral)** — users invite friends and earn free premium after enough successful referrals
- 📊 **Daily Free File Limit** — configurable limit for non-premium users, with verification or upgrade prompts once it's reached
- 📢 **Force-Subscribe (FSUB)** — supports both direct-join and join-request channels, manageable on the fly with `/fsub_nor`, `/fsub_req`, `/delfsub`, `/fsublist` (no restart needed)
- 🌐 **Language Tag in Caption** — automatically detects and shows the file's language
- 🗂️ **Group Management** — settings per group, junk cleanup, broadcast to users/groups, and more

---

## 🤖 Commands

| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/plan` | Check premium pricing |
| `/myplan` | Check your premium subscription status |
| `/settings` | Change group settings |
| `/details` | See current group settings |
| `/reset_group` | Reset group settings |
| `/stats` | Check bot status |
| `/lockmovie` `/unlockmovie` `/lockedlist` | Manage premium-locked movies |
| `/fsub_nor` `/fsub_req` `/delfsub` `/fsublist` | Manage force-subscribe channels |
| `/add_premium` `/remove_premium` `/premium_users` | Manage user premium access |
| `/broadcast` | Broadcast a message to all users |
| `/restart` | Restart the bot |

---

## 🚀 Deployment

This bot is built to run on **Koyeb** (or any host that supports long-running Python workers).

1. Fork/clone this repository
2. Set up a MongoDB database (e.g. MongoDB Atlas — free tier works)
3. Configure the environment variables (see below)
4. Deploy to Koyeb, connected to your GitHub repo
5. Once deployed, use `/index` (in your log channel) to index your movie channels

### Key Environment Variables

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `API_ID` / `API_HASH` | From [my.telegram.org](https://my.telegram.org) |
| `DATABASE_URI` / `DATABASE_NAME` | Your MongoDB connection string |
| `ADMINS` | Telegram user ID(s) of bot admins |
| `AUTH_CHANNEL` / `AUTH_REQ_CHANNEL` | Force-subscribe channels (optional — can also be managed via `/fsub_nor` and `/fsub_req` without restarting) |
| `IS_FILE_LIMIT` / `FREE_FILES` | Enable/configure the daily free-file limit |

> Full list of supported variables is in `info.py`.

---

## 🛠️ Tech Stack

- **[Pyrogram](https://docs.pyrogram.org/)** — Telegram MTProto client
- **MongoDB** — user data, settings, and indexed files
- **[Cinemagoer](https://cinemagoer.readthedocs.io/)** — IMDB data and posters
- **aiohttp** — lightweight web server for health checks / streaming

---

## 📄 License

This project is provided as-is for personal/educational use. Please review and comply with Telegram's Terms of Service and applicable copyright laws in your region when hosting media-sharing bots.
