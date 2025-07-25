# MrAKF2L - Advanced Telegram File to Link Streaming Bot

A powerful Telegram bot that converts files to streamable links with enhanced metadata extraction and professional streaming capabilities.

## 🚀 Features

- **Smart Metadata Extraction**: Automatically extracts quality, season, and episode information from filenames
- **Robust Error Handling**: Safe format dictionaries prevent crashes from missing metadata
- **High Performance**: Optimized for dedicated servers with 12 workers
- **Cloudflare Integration**: Full CDN and security support
- **Professional Streaming**: Clean URLs without port numbers
- **Multi-Client Support**: Handle multiple Telegram sessions
- **Admin Panel**: Complete bot management interface

## 📋 Requirements

- Python 3.8+
- MongoDB Database
- Telegram Bot Token
- Telegram API ID & Hash
- Dedicated Server (recommended)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ArunachalamTech/MrAKF2L.git
cd MrAKF2L
```

2. **Install dependencies:**
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
nano .env
```

4. **Set up your configuration:**
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=your_user_id
DATABASE_URL=your_mongodb_url
FQDN=your_domain.com
```

## 🚀 Deployment

### Local Development
```bash
python3 -m MrAKTech
```

### Production (with nohup)
```bash
nohup python3 -m MrAKTech > /var/log/bot.log 2>&1 &
```

### With Cloudflare Tunnel
```bash
# Setup Cloudflare Tunnel
cloudflared tunnel login
cloudflared tunnel create your-tunnel-name
cloudflared tunnel route dns your-tunnel-name yourdomain.com

# Run tunnel in background
nohup cloudflared tunnel --config ~/.cloudflared/config.yml run your-tunnel-name > /var/log/cloudflared.log 2>&1 &
```

## 📁 Project Structure

```
MrAKF2L/
├── MrAKTech/
│   ├── __init__.py
│   ├── __main__.py
│   ├── clients.py
│   ├── config.py
│   ├── database/
│   ├── plugins/
│   ├── server/
│   └── tools/
│       └── extract_info.py    # Enhanced metadata extraction
├── Storage/
├── requirements.txt
├── runtime.txt
└── README.md
```

## 🔧 Key Enhancements

### Smart Quality Extraction
- Supports: 144p, 240p, 360p, 480p, 720p, 1080p, 4K
- Maps 2160p to 4K automatically
- Returns space for missing/unknown quality

### Episode & Season Detection
- Intelligent pattern matching
- Avoids false positives (years, quality numbers)
- Zero-padded formatting (S01E01)

### Safe Format Dictionary
- Prevents KeyError crashes
- Always provides all placeholders
- Graceful handling of missing data

## 🌐 Server Requirements

### Minimum
- 2 vCores CPU
- 2 GB RAM
- 20 GB Storage
- 100 Mbps Network

### Recommended (High Performance)
- 6 vCores CPU
- 6 GB RAM + 6 GB Virtual RAM
- 80 GB NVMe Storage
- 1 Gbps Network
- Dedicated IP

## 📞 Support

For support and updates:
- **Telegram:** [@IamMrAK_bot](https://telegram.me/IamMrAK_bot)
- **Channel:** [@MrAK_LinkZzz](https://telegram.me/MrAK_LinkZzz)
- **Issues:** [GitHub Issues](https://github.com/ArunachalamTech/MrAKF2L/issues)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**𝙼𝚁𝗔𝗞** - *Initial work* - [ArunachalamTech](https://github.com/ArunachalamTech)

## 🎯 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

⭐ **Star this repository if you find it helpful!**