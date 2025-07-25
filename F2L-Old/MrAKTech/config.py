#Copyright 2021 To 2024-present, Author: MrTamilKiD
 
import os
from os import environ as env
from dotenv import load_dotenv

load_dotenv()

class Telegram:
    MULTI_CLIENT = True
    API_ID = int(env.get("API_ID", "22225617"))
    API_HASH = str(env.get("API_HASH", "ef16f7597376f1689663304c954e4493"))
    BOT_TOKEN = str(env.get("BOT_TOKEN", "7972636771:AAGGC7CzhKQQfqYlkDyqQYT58baIueXSswQ"))
    OWNER_ID = {int(x) for x in os.environ.get("OWNER_ID", "6072149828").split()}
    WORKERS = int(env.get("WORKERS", "16"))  # Increased workers for maximum performance
    DATABASE_URL = str(env.get('DATABASE_URL','mongodb+srv://arunachalamtech:S.Aruna1155@stream.1oiti.mongodb.net/?retryWrites=true&w=majority&appName=stream'))
    DATABASE_NAME = str(env.get('DATABASE_NAME','stream'))
    SLEEP_THRESHOLD = int(env.get("SLEEP_THRESHOLD", "30"))  # Reduced for faster response
    # Performance optimizations
    MAX_CONCURRENT_TRANSMISSIONS = int(env.get("MAX_CONCURRENT_TRANSMISSIONS", "8"))  # Max parallel downloads
    CHUNK_SIZE = int(env.get("CHUNK_SIZE", "2097152"))  # 2MB chunks for better streaming
    CACHE_TIME = int(env.get("CACHE_TIME", "1800"))  # 30 minutes cache for better performance
    FILE_PIC = env.get('FILE_PIC', "https://graph.org/file/8cd764fbdf3ccd34abe22.jpg")
    START_PIC = env.get('START_PIC', "https://graph.org/file/290af25276fa34fa8f0aa.jpg")
    VERIFY_PIC = env.get('VERIFY_PIC', "https://graph.org/file/736e21cc0efa4d8c2a0e4.jpg")
    # Optional command
    FILE_STORE_BOT_TOKEN = str(env.get("FILE_STORE_BOT_TOKEN", "7839112623:AAFL3KbEwNjhmBy6mmPeQL4DlLjIpOu5d3U"))
    FILE_STORE_BOT_USERNAME = str(env.get("FILE_STORE_BOT_USERNAME", "MrAKStreamFileBot"))
    # Channel list
    AUTH_CHANNEL = int(env.get("AUTH_CHANNEL", "-1002467628368"))   # Logs channel for auth channel main
    AUTH_CHANNEL2 = int(env.get("AUTH_CHANNEL2", "-1002839997391")) # Logs channel for auth channel sub
    FLOG_CHANNEL = int(env.get("FLOG_CHANNEL", "-1002844959830"))   # Logs channel for file logs
    ULOG_CHANNEL = int(env.get("ULOG_CHANNEL", "-1002574716230"))   # Logs channel for user logs
    ELOG_CHANNEL = int(env.get("ELOG_CHANNEL", "-1002657841408"))   # Logs channel for error logs
    SULOG_CHANNEL = int(env.get("SULOG_CHANNEL", "-1002686790297")) # Logs channel for storage user logs


    # Channel for bot updates
    SUPPORT = env.get('SUPPORT', "https://telegram.me/IamMrAK_bot")
    BOTNAME = env.get('BOTNAME', "https://telegram.me/MrAKStreamBot")
    MAIN = env.get('MAIN', "https://telegram.me/MrAK_LinkZzz")
    AUTH_GROUP = env.get('AUTH_GROUP', "https://telegram.me/New_Movies_Request_Group_MrAK")
    AUTH_GROUP2 = env.get('AUTH_GROUP2', "https://telegram.me/+aqYAAuHi6HtlOWU9")
    AUTH_CHANNEL3 = env.get('AUTH_CHANNEL3', "https://telegram.me/MrAK_LinkZzz")

    # GroupS List
    REPORT_GROUP = int(env.get("REPORT_GROUP", "-1002189074737"))   # Group for report
class Domain:
    TEMP_URL = str(env.get("FQDN", "https://mraklinkzzz.com/"))
    CHANNEL_URL = str(env.get("CHANNEL_URL", "https://mraklinkzzz.com/")) 
    CLOUDFLARE_URLS = ["https://mraklinkzzz.com/"]  
    MRAKFAST_URLS = ["https://back2flix-617e2bd4caf5.herokuapp.com/"]

class Server:
    PORT = int(env.get("PORT", 8080))  # Standard HTTP port for dedicated server
    BIND_ADDRESS = str(env.get("BIND_ADDRESS", "0.0.0.0"))
    PING_INTERVAL = int(env.get("PING_INTERVAL", "300"))  # Optimized for high performance
    HAS_SSL = str(env.get("HAS_SSL", "1").lower()) in ("1", "true", "t", "yes", "y")  # Enable SSL for security
    NO_PORT = str(env.get("NO_PORT", "1").lower()) in ("1", "true", "t", "yes", "y")  # Clean URLs - no port needed
    FQDN = str(env.get("FQDN", "mraklinkzzz.com"))
    URL = f"https://{FQDN}" if HAS_SSL else f"http://{FQDN}"
    
    # Advanced streaming optimizations
    MAX_CONNECTIONS = int(env.get("MAX_CONNECTIONS", "1000"))  # Max concurrent connections
    KEEPALIVE_TIMEOUT = int(env.get("KEEPALIVE_TIMEOUT", "75"))  # Connection keepalive
    CLIENT_TIMEOUT = int(env.get("CLIENT_TIMEOUT", "300"))  # Client timeout
    BUFFER_SIZE = int(env.get("BUFFER_SIZE", "65536"))  # 64KB buffer for streaming

    # Default link mode caption
    DEFAULT_LINK_MODE_CAPTION = str(env.get('DEFAULT_LINK_MODE_CAPTION', """<b>{filenamefirst}

❤️‍🔥 Uploaded By - [♻️@MrAK_LinkZzz](https://telegram.me/MrAK_LinkZzz)

{file_size} : {stream_link}

<a href="https://telegram.me/MrAK_LinkZzz">Join</a></b>"""))    

