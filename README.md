# TRMNL Discord Bot

The official Discord bot for the TRMNL community. This bot provides easy access to TRMNL documentation, resources, and updates directly within Discord.

## Features

- Access to TRMNL documentation and resources
- Latest news and updates about TRMNL
- DIY TRMNL guides and information
- Privacy policy and terms of service information
- Framework documentation access

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- A Discord Bot Token
- Discord Developer Application access

### Configuration

1. Clone this repository:
```bash
git clone https://github.com/usetrmnl/discord-bot.git
cd discord-bot
```

2. Create and configure environment variables:
   - Copy `.env.template` to `.env`
   - Add your Discord bot token:
```bash
DISCORD_TOKEN=your_bot_token_here
```

3. Configure `config.json`:
   - Set your desired command prefix
   - Add your bot's invite link

### Installation

1. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Running the Bot

```bash
python bot.py
```

## Command Reference

- `/home` - Main TRMNL resources
- `/docs` - Documentation links
- `/framework` - Framework documentation
- `/news` - Latest updates
- `/updates` - All blog posts
- `/privacy` - Privacy policy
- `/terms` - Terms of service
- `/diy` - DIY TRMNL information

## Development

### Adding New Commands

Commands are managed in `src/bot/trmnl.py`. Each command is implemented as a slash command using Discord.py's hybrid command system.

### Documentation Updates

Resource links and documentation content are managed in `docs.json`. Update this file to modify command responses.

## Support

Need help? Join the [TRMNL Discord Community](https://discord.gg/trmnl)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is proprietary software owned by TRMNL. All rights reserved.