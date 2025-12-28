# qBittorrent Telegram Bot

A lightweight Telegram bot that reports qBittorrent download status. Runs locally and polls Telegram servers outbound, so no port forwarding or public exposure required.

## Features

- `/status` - Show all torrents with progress bars
- `/downloads` - Show only active downloads
- `/speed` - Current transfer speeds
- `/help` - Command list
- Chat ID allowlist for access control
- Visual progress bars and status emojis

## How It Works

```
[Telegram Servers] <──outbound polling── [Bot Container] ──local──> [qBittorrent]
     (internet)                            (your LAN)                (your LAN)
```

The bot makes **outbound** HTTPS connections to poll Telegram for messages. qBittorrent stays safely on your local network with no exposure.

## Quick Start

### 1. Clone the Repository

```bash
cd /opt/docker # or wherever you will be running this project
git clone https://github.com/YOUR_USERNAME/qbit-telegram-bot.git
cd qbit-telegram-bot
```

### 2. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow prompts
3. Copy the API token

### 3. Get Your Chat ID

Send a message to your new bot, then visit:
```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```
Look for `"chat":{"id":` in the response.

### 3. Configure

Edit `docker-compose.yml`:

```yaml
environment:
  - TELEGRAM_TOKEN=your_bot_token_here
  - QBIT_HOST=http://localhost:8080  # your qBittorrent IP
  - QBIT_USER=admin                  # your Qbittorrent Web UI Username
  - QBIT_PASS=adminadmin             # your Qbittorrent Web UI Password
  - ALLOWED_CHAT_IDS=-123456789      # your chat ID, or leave empty
```

### 4. Run

```bash
docker compose up -d --build
```

### 5. Register Commands (Optional)

Message @BotFather:
```
/setcommands
```
Then send:
```
status - Show all torrents
downloads - Show active downloads only
speed - Current transfer speeds
help - Show available commands
```

## Network Modes

### Host Networking (Default)

Best when qBittorrent runs on the same machine:

```yaml
network_mode: host
```

### Bridge Networking

If qBittorrent is on another machine:

```yaml
# Remove network_mode: host and use default bridge
environment:
  - QBIT_HOST=http://192.168.1.100:8080
```

### Macvlan

If you need the container to have its own IP:

```yaml
networks:
  macvlan:
    external: true
    ipv4_address: 192.168.0.200 # Example IP
    mac_address: 88:7C:54:6C:53:A3 # If you would also like to specify a MAC address
```

## Group Chat Setup

If using in a Telegram group:

1. Add the bot to the group
2. Message @BotFather: `/setprivacy` → Select bot → Disable
3. Remove and re-add the bot to the group

## Troubleshooting

**Bot not responding in group:**
- Disable privacy mode via @BotFather
- Remove and re-add bot to group

**Can't connect to qBittorrent:**
- Verify Web UI is enabled in qBittorrent settings
- Check URL/credentials work in browser
- Ensure container can reach qBittorrent (network mode)

**"Unauthorized" message:**
- Your chat ID isn't in `ALLOWED_CHAT_IDS`
- The bot tells you your chat ID in the error message

## License

MIT
