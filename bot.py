#!/usr/bin/env python3
"""
Telegram bot for qBittorrent download status.
Polls Telegram servers outbound - no inbound connections needed.
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from qbittorrentapi import Client, LoginFailed

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config from environment
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
QBIT_HOST = os.environ.get("QBIT_HOST", "http://localhost:8080")
QBIT_USER = os.environ.get("QBIT_USER", "admin")
QBIT_PASS = os.environ.get("QBIT_PASS", "adminadmin")
ALLOWED_CHAT_IDS = os.environ.get("ALLOWED_CHAT_IDS", "").split(",")


def get_qbit_client() -> Client:
    """Create and authenticate qBittorrent client."""
    client = Client(host=QBIT_HOST, username=QBIT_USER, password=QBIT_PASS)
    client.auth_log_in()
    return client


def format_size(bytes_val: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def format_speed(bytes_per_sec: int) -> str:
    """Convert bytes/sec to human readable format."""
    return f"{format_size(bytes_per_sec)}/s"


def format_eta(seconds: int) -> str:
    """Convert seconds to human readable ETA."""
    if seconds < 0 or seconds == 8640000:  # qBit uses 8640000 for infinity
        return "∞"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def get_status_emoji(state: str) -> str:
    """Map qBittorrent state to emoji."""
    state_map = {
        "downloading": "⬇️",
        "uploading": "⬆️",
        "stalledDL": "⏸️",
        "stalledUP": "📤",
        "pausedDL": "⏹️",
        "pausedUP": "⏹️",
        "queuedDL": "🕐",
        "queuedUP": "🕐",
        "checkingDL": "🔍",
        "checkingUP": "🔍",
        "error": "❌",
        "missingFiles": "⚠️",
        "metaDL": "📥",
        "forcedDL": "⏬",
        "allocating": "💾",
        "moving": "📁",
    }
    return state_map.get(state, "❓")


async def check_allowed(update: Update) -> bool:
    """Check if chat is allowed to use the bot."""
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHAT_IDS and ALLOWED_CHAT_IDS[0]:
        if chat_id not in ALLOWED_CHAT_IDS:
            logger.warning(f"Unauthorized access attempt from chat_id: {chat_id}")
            await update.message.reply_text("⛔ Unauthorized. Your chat ID: " + chat_id)
            return False
    return True


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show all torrents."""
    if not await check_allowed(update):
        return

    try:
        client = get_qbit_client()
        torrents = client.torrents_info()
        
        if not torrents:
            await update.message.reply_text("✅ No torrents!")
            return

        lines = ["📊 *Torrents*", ""]
        
        for t in torrents[:10]:
            emoji = get_status_emoji(t.state)
            progress = t.progress * 100
            name = t.name[:45] + "…" if len(t.name) > 45 else t.name
            
            filled = int(progress / 5)
            bar = "▓" * filled + "░" * (20 - filled)
            
            lines.append(f"{emoji} *{name}*")
            lines.append(f"`{bar}` {progress:.0f}%")
            
            stats = f"{format_size(t.downloaded)}/{format_size(t.size)}"
            if t.dlspeed > 0:
                stats += f" • ⬇️ {format_speed(t.dlspeed)}"
            if t.state == "downloading" and t.eta > 0 and t.eta != 8640000:
                stats += f" • 🕐 {format_eta(t.eta)}"
            lines.append(stats)
            lines.append("")

        if len(torrents) > 10:
            lines.append(f"_+{len(torrents) - 10} more..._")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except LoginFailed:
        logger.error("qBittorrent login failed")
        await update.message.reply_text("❌ Failed to connect to qBittorrent. Check credentials.")
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def downloads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /downloads command - show only downloading torrents."""
    if not await check_allowed(update):
        return

    try:
        client = get_qbit_client()
        torrents = client.torrents_info(status_filter="downloading")
        
        if not torrents:
            await update.message.reply_text("✅ Nothing downloading!")
            return

        lines = ["⬇️ *Downloading*", ""]
        
        for t in torrents[:10]:
            progress = t.progress * 100
            name = t.name[:45] + "…" if len(t.name) > 45 else t.name
            
            filled = int(progress / 5)
            bar = "▓" * filled + "░" * (20 - filled)
            
            lines.append(f"*{name}*")
            lines.append(f"`{bar}` {progress:.0f}%")
            lines.append(f"⬇️ {format_speed(t.dlspeed)} • 🕐 {format_eta(t.eta)}")
            lines.append("")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error fetching downloads: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /speed command - show current transfer speeds."""
    if not await check_allowed(update):
        return

    try:
        client = get_qbit_client()
        info = client.transfer_info()
        
        msg = "📈 *Transfer Speeds*\n\n"
        msg += f"⬇️ Download: {format_speed(info['dl_info_speed'])}\n"
        msg += f"⬆️ Upload: {format_speed(info['up_info_speed'])}\n\n"
        msg += f"📥 Session DL: {format_size(info['dl_info_data'])}\n"
        msg += f"📤 Session UP: {format_size(info['up_info_data'])}"
        
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error fetching speed: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not await check_allowed(update):
        return

    msg = """🏴‍☠️ *qBittorrent Status Bot*

*Commands:*
/status - All torrents
/downloads - Currently downloading only  
/speed - Current transfer speeds
/help - This message"""
    
    await update.message.reply_text(msg, parse_mode="Markdown")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("downloads", downloads))
    app.add_handler(CommandHandler("speed", speed))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
