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
- Added DocCache system for documentation performance
- Added TRMNLMetrics for command tracking
- Added HealthMonitor for bot performance monitoring
- Added BotLogger for improved logging
- Improved error handling with detailed error tracking
- Enhanced rate limiting system
- Added message component support
- Added feedback channel configuration

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
- **DocCache System**
  - Improved documentation loading performance
  - TTL-based cache invalidation
  - Reduced API load
  
- **TRMNLMetrics**
  - Command usage tracking
  - Admin action logging
  - Error tracking and analysis
  - Usage statistics

- **HealthMonitor**
  - Uptime tracking
  - Command count monitoring
  - Error rate monitoring
  - Guild count tracking
  - Performance metrics

- **BotLogger**
  - Configurable logging levels
  - Command execution logging
  - Error tracking with context
  - Discord.py event logging

- **Rate Limiting**
  - Enhanced bucket management
  - Global rate limit handling
  - Invalid request tracking
  - Cloudflare ban prevention
  - Detailed rate limit feedback

### Bug Fixes
- Fixed inconsistent error handling
- Improved command failure recovery
- Enhanced rate limit precision
- Fixed documentation reload issues
- Improved error message clarity

### Requirements
```
Python 3.11+
discord.py 2.3.0+
python-dotenv 1.0.0+
aiohttp 3.8.0+
typing-extensions 4.7.0+
pytest 7.4.0+
pytest-asyncio 0.21.1+
pytest-cov 4.1.0+
```

---

## Previous Releases

### Version 1.0.0
*Released December 23, 2024*

Initial release with core documentation access commands, basic slash command structure, and rate limiting system.

#### Features
- Core documentation access commands
- Basic slash command structure
- Initial rate limiting system
- TRMNL documentation integration
- Basic error handling
- Admin commands for maintenance

#### Commands
- `/home` - Main TRMNL resources
- `/docs` - Documentation links
- `/framework` - Framework documentation
- `/news` - Latest updates
- `/updates` - All blog posts
- `/privacy` - Privacy policy
- `/terms` - Terms of service
- `/diy` - DIY TRMNL information

#### Admin Commands
- `/sync` - Sync slash commands
- `/reload_docs` - Reload documentation cache

---

*For more detailed information about setup and usage, please see the [main README](README.md).*