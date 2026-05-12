from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import os
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 🔑 CONFIG
TOKEN = os.getenv("8675240270:AAFr1QF-oLLcVXAnjniPWIqBhiXjTB9eyqI") or "8675240270:AAFr1QF-oLLcVXAnjniPWIqBhiXjTB9eyqI"
CANAL = "@yesterpreuwba"
OWNER_ID = 7752782654

# 📁 CARPETA SEGURA
CARPETA = os.path.join(os.getenv("APPDATA") or ".", "RefesBot")
os.makedirs(CARPETA, exist_ok=True)

ARCHIVO_DATOS = os.path.join(CARPETA, "datos.json")
ARCHIVO_USERS = os.path.join(CARPETA, "users.json")
ARCHIVO_ADMINS = os.path.join(CARPETA, "admins.json")


# 📂 CARGAR
def cargar(path):
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}


# 💾 GUARDAR
def guardar(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


# 🔐 ROLES
def es_owner(user_id):
    return user_id == OWNER_ID


def es_admin(user_id):
    admins = cargar(ARCHIVO_ADMINS)
    return str(user_id) in admins or es_owner(user_id)


def puede_refes(user_id):
    users = cargar(ARCHIVO_USERS)
    return str(user_id) in users or es_admin(user_id)


# 👤 ADD USER (solo refes)
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_owner(update.message.from_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usa: /adduser ID")
        return

    user_id = context.args[0]
    users = cargar(ARCHIVO_USERS)
    users[user_id] = True
    guardar(ARCHIVO_USERS, users)

    await update.message.reply_text(f"👤 Usuario agregado: {user_id}")


# 🛡️ ADD ADMIN
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_owner(update.message.from_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usa: /addadmin ID")
        return

    user_id = context.args[0]
    admins = cargar(ARCHIVO_ADMINS)
    admins[user_id] = True
    guardar(ARCHIVO_ADMINS, admins)

    await update.message.reply_text(f"🛡️ Admin agregado: {user_id}")


# ❌ REMOVE
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_owner(update.message.from_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usa: /remove ID")
        return

    user_id = context.args[0]

    admins = cargar(ARCHIVO_ADMINS)
    users = cargar(ARCHIVO_USERS)

    if user_id in admins:
        del admins[user_id]
        guardar(ARCHIVO_ADMINS, admins)

    if user_id in users:
        del users[user_id]
        guardar(ARCHIVO_USERS, users)

    await update.message.reply_text(f"❌ Usuario eliminado: {user_id}")


# 🔄 RESET
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.message.from_user.id):
        return

    guardar(ARCHIVO_DATOS, {})
    await update.message.reply_text("🔄 Contadores reiniciados")


# 📊 REPORTE
async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.message.from_user.id):
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usa: /reporte abril 18 22")
        return

    mes_texto = context.args[0].lower()
    inicio = int(context.args[1])
    fin = int(context.args[2])

    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }

    if mes_texto not in meses:
        await update.message.reply_text("Mes inválido")
        return

    mes_num = meses[mes_texto]
    datos = cargar(ARCHIVO_DATOS)
    resumen = {}

    for user_id, info in datos.items():
        for ref in info.get("historial", []):
            fecha = datetime.strptime(ref["fecha"], "%Y-%m-%d")

            if fecha.month == mes_num and inicio <= fecha.day <= fin:
                resumen[user_id] = resumen.get(user_id, 0) + 1

    if not resumen:
        await update.message.reply_text("No hay datos")
        return

    texto = f"📊 REPORTE ({mes_texto} {inicio}-{fin})\n\n"
    for user_id, total in resumen.items():
        texto += f"ID {user_id}: {total} refes\n"

    await update.message.reply_text(texto)


# 🚀 .refes
async def refes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg or not puede_refes(msg.from_user.id):
        return

    if msg.text and msg.text.startswith("/"):
        return

    if not msg.text or not msg.text.lower().startswith(".refes"):
        return

    if not msg.reply_to_message:
        await msg.reply_text("Responde al mensaje")
        return

    original = msg.reply_to_message

    user = msg.from_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else user.first_name
    grupo = msg.chat.title

    datos = cargar(ARCHIVO_DATOS)

    if user_id not in datos:
        datos[user_id] = {"count": 0, "historial": []}

    datos[user_id]["count"] += 1
    datos[user_id]["historial"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d")
    })

    guardar(ARCHIVO_DATOS, datos)

    numero = datos[user_id]["count"]

    caption = (
        f"👑 ADMIN AYLES: {username}\n\n"
        f"""```
🛍️ REFES NUEVO

📊 Tus refes: #{numero}

💬 Descripción:
GRACIAS POR ELEGIRNOS
VUELVE PRONTO

━━━━━━━━━━━━━━
📢 Grupo: {grupo}
```"""
    )

    await context.bot.copy_message(
        chat_id=CANAL,
        from_chat_id=original.chat_id,
        message_id=original.message_id,
        caption=caption,
        parse_mode="Markdown"
    )


# 🌐 SERVIDOR PARA RENDER (NO SE DUERMA)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


threading.Thread(target=run_server).start()


# ▶️ INICIAR BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("addadmin", addadmin))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("reporte", reporte))
app.add_handler(MessageHandler(filters.Regex(r"^\.reset$"), reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, refes))

print("Bot 24/7 funcionando en Render 🚀")
app.run_polling()

