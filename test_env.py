from dotenv import load_dotenv
import os

load_dotenv()  # Carga variables del archivo .env

token = os.getenv("TELEGRAM_TOKEN")

if token:
    print("✅ Token cargado correctamente:", token[:10] + "...")
else:
    print("❌ No se pudo cargar el token. Revisa tu archivo .env")
