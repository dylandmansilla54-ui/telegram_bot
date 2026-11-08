import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configurar logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Diccionario temporal en memoria
user_notes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"¡Hola {user_name}! 📝 Soy tu bot bloc de notas alojado en la nube.\n\n"
        "Comandos:\n"
        "• Envía texto para guardarlo como nota.\n"
        "• Envía un archivo `.txt` para guardarlo.\n"
        "• /notas - Ver tus notas.\n"
        "• /exportar - Recibir tus notas en un archivo .txt."
    )

async def save_text_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_notes:
        user_notes[user_id] = []
    
    note_title = text.split('\n')[0][:30]
    user_notes[user_id].append({"title": note_title, "content": text})
    await update.message.reply_text(f"✅ Nota guardada:\n*{note_title}*", parse_mode="Markdown")

async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    notes = user_notes.get(user_id, [])
    
    if not notes:
        await update.message.reply_text("📭 Aún no tienes notas guardadas.")
        return
    
    response = "📋 *Tus Notas Guardadas:*\n\n"
    for i, note in enumerate(notes, 1):
        response += f"{i}. {note['title']}\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def export_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    notes = user_notes.get(user_id, [])
    
    if not notes:
        await update.message.reply_text("📭 No hay notas para exportar.")
        return
    
    file_path = f"notas_{user_id}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for i, note in enumerate(notes, 1):
            f.write(f"--- Nota {i}: {note['title']} ---\n")
            f.write(f"{note['content']}\n\n")
            
    with open(file_path, "rb") as f:
        await update.message.reply_document(document=f, filename="mis_notas.txt", caption="Aquí tienes tu archivo de notas 📄")
        
    os.remove(file_path)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    document = update.message.document
    
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("⚠️ Solo puedo procesar archivos con extensión .txt")
        return
    
    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()
    text_content = file_content.decode("utf-8")
    
    if user_id not in user_notes:
        user_notes[user_id] = []
        
    user_notes[user_id].append({"title": document.file_name, "content": text_content})
    await update.message.reply_text(f"📥 Archivo `{document.file_name}` importado como nota.", parse_mode="Markdown")

def main():
    TOKEN = os.environ.get("TOKEN")
    PORT = int(os.environ.get("PORT", "8443"))
    # Render asigna una URL pública automática a tu servicio web
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("notas", list_notes))
    app.add_handler(CommandHandler("exportar", export_txt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_text_note))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("🤖 Iniciando bot en la nube con Webhooks...")
    
    # Arrancar el bot escuchando mediante Webhooks para Render
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        secret_token="mi_token_secreto_seguro",
        webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()