import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import config
from youtube_service import search_and_add
import pytz

DB = 'db.sqlite'

# -------------------------
# Inicializar base de datos
# -------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    title TEXT,
                    status TEXT DEFAULT 'pending'
                )""")
    conn.commit()
    conn.close()

def add_song(user, title):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO songs (user, title) VALUES (?, ?)", (user, title))
    conn.commit()
    conn.close()

def get_pending():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, user, title FROM songs WHERE status='pending' ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def set_status(song_id, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE songs SET status=? WHERE id=?", (status, song_id))
    conn.commit()
    conn.close()

# -------------------------
# Helper para reply
# -------------------------
async def safe_reply(update: Update, text: str):
    msg = update.message
    if msg:
        await msg.reply_text(text)

# -------------------------
# Handlers de Telegram
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update,
        "🎧🔥 ¡Hola! Soy el DJ de la Guarida de Neumus! 💿😈\n"
        "Envía el nombre de la canción y artista, ejemplo: Bohemian Rhapsody - Queen\n\n"
        "Recuerda: Buenos fumes y morbo 😈"
    )

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_pending()
    if not rows:
        await safe_reply(update, "No hay canciones pendientes.")
        return
    msg = "Canciones pendientes:\n"
    for r in rows:
        msg += f"{r[0]} - {r[2]} (por {r[1]})\n"
    await safe_reply(update, msg)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await safe_reply(update, "Usa /approve <ID>")
        return
    try:
        song_id = int(context.args[0])
    except ValueError:
        await safe_reply(update, "ID inválido")
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT title FROM songs WHERE id=? AND status='pending'", (song_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        await safe_reply(update, "No existe canción pendiente con ese ID.")
        return

    title = row[0]
    await safe_reply(update, "Buscando en YouTube y añadiendo a la playlist...")
    try:
        res = search_and_add(title, config.PLAYLIST_ID)
        if res['status'] == 'duplicate':
            set_status(song_id, 'duplicate')
            await safe_reply(update, "La canción ya estaba en la playlist, marcada como duplicada.")
        else:
            set_status(song_id, 'approved')
            await safe_reply(update, "✅ Añadida a la playlist privada.")
    except Exception as e:
        await safe_reply(update, f"Error al añadir: {e}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await safe_reply(update, "Usa /delete <ID>")
        return
    try:
        song_id = int(context.args[0])
    except ValueError:
        await safe_reply(update, "No hay canciones pendientes.")
