# config.py  (новая версия)
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN           = os.getenv("TELEGRAM_TOKEN")
YOOKASSA_PROVIDER_TOKEN  = os.getenv("YOOKASSA_PROVIDER_TOKEN")
YOOKASSA_SHOP_ID         = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY      = os.getenv("YOOKASSA_SECRET_KEY")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME     = os.getenv("DB_NAME")