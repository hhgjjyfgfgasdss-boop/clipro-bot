import os
import asyncio
import tempfile
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import google.generativeai as genai

# ==========================================
# ตั้งค่า API Keys (ใส่ใน Railway Environment Variables)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ==========================================
# เก็บ state ของแต่ละ user
# ==========================================
user_history = {}   # { user_id: [ {"role": "user/model", "parts": [...]} ] }
user_mode    = {}   # { user_id: "transcribe" | "edit" | "sound" | "script" | "analyze" | "trend" | "chat" }

# ==========================================
# System Prompt ของบอท
# ==========================================
SYSTEM_PROMPT = """คุณคือ "คลิปโปร" AI ผู้ช่วยสำหรับ Content Creator และ Video Editor ชาวไทย

ความสามารถหลัก:
1. ถอดเสียงจากคลิปหรือไฟล์เสียงเป็นข้อความภาษาไทย
2. แนะนำการตัดต่อ: จุดตัด B-Roll ฟุต transition จังหวะ
3. แนะนำเพลง/ซาวด์ประกอบที่เข้ากับอารมณ์คลิป
4. คิดบท สคริปต์ ที่โดดเด่นและน่าสนใจ
5. วิเคราะห์คลิปสำเร็จรูปและให้คำแนะนำปรับปรุง
6. ติดตามเทรนด์คลิปและแนะนำสไตล์ใหม่ๆ

สไตล์การตอบ: ภาษาไทย, กระชับ, ใช้ emoji, ให้คำแนะนำที่นำไปใช้ได้จริง"""


# ==========================================
# เรียก Gemini
# ==========================================
async def ask_gemini(user_id: int, message: str, media_b64=None, mime_type=None) -> str:
    if user_id not in user_history:
        user_history[user_id] = []

    parts = []
    if media_b64 and mime_type:
        parts.append({"inline_data": {"mime_type": mime_type, "data": media_b64}})
    parts.append(message)

    user_history[user_id].append({"role": "user", "parts": parts})
    history = user_history[user_id][-10:]

    try:
        chat = model.start_chat(history=history[:-1])
        response = await asyncio.to_thread(
            chat.send_message,
            history[-1]["parts"],
            generation_config={"temperature": 0.7, "max_output_tokens": 2048}
        )
        reply = response.text
        user_history[user_id].append({"role": "model", "parts": [reply]})
        return reply
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}\nลองใหม่อีกครั้งนะครับ"


# ==========================================
# เมนูหลัก
# ==========================================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎙️ ถอดเสียงเป็นข้อความ", callback_data="mode_transcribe")],
        [
            InlineKeyboardButton("✂️ แนะนำการตัดต่อ", callback_data="mode_edit"),
            InlineKeyboardButton("🎵 แนะนำซาวด์", callback_data="mode_sound"),
        ],
        [
            InlineKeyboardButton("📝 คิดบท/สคริปต์", callback_data="mode_script"),
            InlineKeyboardButton("🔍 วิเคราะห์คลิป", callback_data="mode_analyze"),
        ],
        [InlineKeyboardButton("📈 เทรนด์คลิปใหม่", callback_data="mode_trend")],
        [InlineKeyboardButton("💬 สนทนาทั่วไป", callback_data="mode_chat")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==========================================
# Commands
# ==========================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_mode[user.id] = "chat"
    await update.message.reply_text(
        f"สวัสดีครับ {user.first_name}! 👋\n\n"
        "ผมคือ *คลิปโปร* 🎬 AI ผู้ช่วยสำหรับ Content Creator\n\n"
        "เลือกสิ่งที่ต้องการได้เลยครับ 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("เลือกโหมดได้เลยครับ 👇", reply_markup=main_menu())

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_history[uid] = []
    user_mode[uid] = "chat"
    await update.message.reply_text("🗑️ ล้างประวัติแล้วครับ เริ่มใหม่ได้เลย!")


# ==========================================
# Callback เมื่อกดปุ่ม
# ==========================================
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    modes = {
        "mode_transcribe": ("transcribe", "🎙️ *โหมดถอดเสียง*\nส่งไฟล์เสียงหรือวิดีโอมาได้เลยครับ"),
        "mode_edit":       ("edit",       "✂️ *โหมดแนะนำการตัดต่อ*\nวางบทหรืออธิบายคลิปให้ผมฟังครับ"),
        "mode_sound":      ("sound",      "🎵 *โหมดแนะนำซาวด์*\nบอกอารมณ์คลิปหรือส่งบทมาได้เลยครับ"),
        "mode_script":     ("script",     "📝 *โหมดคิดบท/สคริปต์*\nบอก topic ที่อยากทำได้เลยครับ"),
        "mode_analyze":    ("analyze",    "🔍 *โหมดวิเคราะห์คลิป*\nส่งบทหรืออธิบายคลิปที่ทำเสร็จแล้วได้เลยครับ"),
        "mode_trend":      ("trend",      "📈 *โหมดเทรนด์คลิป*\nถามเรื่องเทรนด์ คำฮิต สไตล์ใหม่ๆ ได้เลยครับ"),
        "mode_chat":       ("chat",       "💬 *โหมดสนทนาทั่วไป*\nถามอะไรก็ได้เลยครับ"),
    }

    if q.data in modes:
        mode, text = modes[q.data]
        user_mode[uid] = mode
        await q.edit_message_text(text, parse_mode="Markdown")


# ==========================================
# รับข้อความ
# ==========================================
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    text = update.message.text
    mode = user_mode.get(uid, "chat")

    prompts = {
        "transcribe": f"{SYSTEM_PROMPT}\n\nผู้ใช้ถามเกี่ยวกับการถอดเสียง: {text}",
        "edit":       f"{SYSTEM_PROMPT}\n\nวิเคราะห์และแนะนำการตัดต่อสำหรับ:\n{text}\n\nให้แนะนำ: จุดตัด, B-Roll, transition, จังหวะ",
        "sound":      f"{SYSTEM_PROMPT}\n\nแนะนำซาวด์/เพลงสำหรับ:\n{text}\n\nให้แนะนำ: สไตล์เพลง, SFX, platform ที่หาเพลงฟรีได้",
        "script":     f"{SYSTEM_PROMPT}\n\nเขียนบทหรือสคริปต์สำหรับ:\n{text}\n\nต้องมี: hook ใน 3 วิแรก, เนื้อหาน่าสนใจ, CTA ชัดเจน",
        "analyze":    f"{SYSTEM_PROMPT}\n\nวิเคราะห์คลิปนี้:\n{text}\n\nให้คะแนน 1-10 และแนะนำ: จุดแข็ง, จุดที่ควรแก้, วิธีปรับ",
        "trend":      f"{SYSTEM_PROMPT}\n\nให้ข้อมูลเทรนด์เกี่ยวกับ: {text}\n\nแนะนำสไตล์ใหม่ คำฮิต และวิธีนำไปใช้",
        "chat":       f"{SYSTEM_PROMPT}\n\nผู้ใช้ถามว่า: {text}",
    }

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await ask_gemini(uid, prompts.get(mode, text))
    await update.message.reply_text(reply, parse_mode="Markdown")


# ==========================================
# รับไฟล์เสียง
# ==========================================
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text("🎙️ รับไฟล์เสียงแล้ว กำลังถอดเสียง โปรดรอสักครู่...")

    try:
        if update.message.voice:
            file_obj = await update.message.voice.get_file()
            mime = "audio/ogg"
            suffix = ".ogg"
        else:
            file_obj = await update.message.audio.get_file()
            mime = "audio/mpeg"
            suffix = ".mp3"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await file_obj.download_to_drive(tmp.name)
            audio_b64 = base64.b64encode(open(tmp.name, "rb").read()).decode()

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "ถอดเสียงในไฟล์นี้ให้ครบถ้วนแม่นยำเป็นภาษาไทย "
            "จากนั้นสรุปใจความสำคัญสั้นๆ "
            "แล้วถามว่าต้องการให้ช่วยอะไรต่อ (ตัดต่อ / คิดบท / วิเคราะห์)"
        )
        reply = await ask_gemini(uid, prompt, audio_b64, mime)
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ ถอดเสียงไม่สำเร็จ: {str(e)}")


# ==========================================
# รับวิดีโอ
# ==========================================
async def on_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    mode = user_mode.get(uid, "analyze")
    await update.message.reply_text("🎬 รับวิดีโอแล้ว กำลังวิเคราะห์ โปรดรอสักครู่...")

    try:
        vfile = update.message.video or update.message.video_note
        file_obj = await vfile.get_file()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await file_obj.download_to_drive(tmp.name)
            video_b64 = base64.b64encode(open(tmp.name, "rb").read()).decode()

        task = {
            "transcribe": "ถอดเสียงพูดในวิดีโอนี้ให้ครบถ้วน พร้อม timestamp โดยประมาณ",
            "edit":       "วิเคราะห์วิดีโอและแนะนำ: จุดตัด B-Roll transition จังหวะการตัดต่อ",
            "sound":      "ดูวิดีโอแล้วแนะนำเพลงประกอบและ SFX ที่เหมาะกับอารมณ์และเนื้อหา",
            "analyze":    "วิเคราะห์คลิปแบบละเอียด: hook, การดำเนินเรื่อง, จุดดี, จุดที่ควรปรับ พร้อมคะแนน 1-10",
            "script":     "ดูวิดีโอแล้วช่วยเขียนหรือปรับบทให้น่าสนใจกว่าเดิม",
            "chat":       "วิเคราะห์วิดีโอนี้และแนะนำสิ่งที่น่าสนใจ",
        }.get(mode, "วิเคราะห์วิดีโอนี้")

        reply = await ask_gemini(uid, f"{SYSTEM_PROMPT}\n\n{task}", video_b64, "video/mp4")
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            f"❌ ไม่สำเร็จ: {str(e)}\n"
            "หมายเหตุ: Gemini รองรับวิดีโอสูงสุด ~10MB ครับ"
        )


# ==========================================
# Main
# ==========================================
def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("❌ กรุณาตั้งค่า TELEGRAM_TOKEN และ GEMINI_API_KEY")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu",  cmd_menu))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, on_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("✅ คลิปโปร บอทเริ่มทำงานแล้ว!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
