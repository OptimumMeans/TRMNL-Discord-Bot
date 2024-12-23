# TRMNL Discord Bot Updates

## Latest Release - Version 2.0.0
*Released December 23, 2024*

### Major Features
- Added search functionality for documentation
- Added status monitoring and metrics
- Added feedback system with dedicated channel
- Added support command and resources
- Added changelog command
- Added pipeline/roadmap command
- Improved error handling and logging
- Added message component support
- Added documentation caching system
- Added metrics tracking

### New Commands
| Command | Description |
|---------|-------------|
| `/search` | Search TRMNL documentation |
| `/status` | Show bot status and metrics |
| `/support` | Get support information |
| `/feedback` | Submit feedback |
| `/changelog` | View recent updates |
| `/pipeline` | See upcoming features |

### Technical Improvements
- Added DocCache system for performance
- Added TRMNLMetrics for usage tracking
- Improved error handling with detailed logging
- Enhanced rate limiting system
- Added support for message components
- Added feedback channel configuration

### Requirements
```
Python 3.11+
discord.py 2.3.0+
python-dotenv 1.0.0+
aiohttp 3.8.0+
```

---

## Previous Releases

### Version 1.0.0
*Released December 23, 2024*

Initial release with core documentation access commands, basic slash command structure, and rate limiting system. Added basic commands for accessing TRMNL resources, documentation, and DIY information. Implemented admin commands for syncing and reloading documentation.

---

*For more detailed information about setup and usage, please see the [main README](README.md).*