# config.py  (новая версия)
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN           = os.getenv("TELEGRAM_TOKEN")
YOOKASSA_PROVIDER_TOKEN  = os.getenv("YOOKASSA_PROVIDER_TOKEN")
YOOKASSA_SHOP_ID         = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY      = os.getenv("YOOKASSA_SECRET_KEY")