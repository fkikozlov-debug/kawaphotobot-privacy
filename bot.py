import os
import base64
import logging
import tempfile
from pathlib import Path

from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kawaiiphotobot")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

ai = OpenAI(api_key=OPENAI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "୨୧ Привет! Я KawaiiPhotoBot 🎀\n\n"
        "/cute текст — оформить текст в няшном стиле\n"
        "/generate описание — создать картинку\n"
        "Чтобы изменить фото, отправь его с подписью:\n"
        "/edit добавь розовые бантики и пастельный фон\n"
        "/help — помощь"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎀 Команды:\n"
        "/start — запуск\n"
        "/cute текст — няшное оформление текста\n"
        "/generate описание — создание AI-картинки\n"
        "/edit описание — редактирование фото (команда в подписи к фото)\n"
        "/help — помощь"
    )


async def cute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.message.reply_text("Напиши текст после /cute.")
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        result = ai.responses.create(
            model=TEXT_MODEL,
            instructions=(
                "Rewrite the user's text in a cute kawaii aesthetic. "
                "Preserve its meaning and language. Add tasteful symbols such as "
                "୨୧, ♡, 🎀, ✨ and 🌸. Return only the rewritten text."
            ),
            input=prompt,
        )
        answer = result.output_text.strip()
        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i + 4000])
    except Exception:
        log.exception("Text styling error")
        await update.message.reply_text("Не получилось оформить текст. Проверь настройки AI API.")


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.message.reply_text("Напиши описание картинки после /generate.")
        return
    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    try:
        result = ai.images.generate(
            model=IMAGE_MODEL,
            prompt=(
                "Create a polished cute kawaii aesthetic image with tasteful pastel "
                "colors, soft lighting and detailed composition. User request: " + prompt
            ),
            size="1024x1024",
        )
        image_bytes = base64.b64decode(result.data[0].b64_json)
        await update.message.reply_photo(photo=image_bytes, caption="୨୧ Готово! 🎀")
    except Exception:
        log.exception("Image generation error")
        await update.message.reply_text("Не удалось создать изображение. Проверь доступ к Image API и оплату API.")


async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.photo:
        await msg.reply_text("Отправь фото с подписью /edit и описанием изменений.")
        return
    prompt = (msg.caption or "").replace("/edit", "", 1).strip()
    if not prompt:
        await msg.reply_text("Добавь описание после /edit в подпись к фото.")
        return

    temp_path = None
    await msg.chat.send_action(ChatAction.UPLOAD_PHOTO)
    try:
        photo_file = await context.bot.get_file(msg.photo[-1].file_id)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            temp_path = tmp.name
        await photo_file.download_to_drive(custom_path=temp_path)

        with open(temp_path, "rb") as image_file:
            result = ai.images.edit(
                model=IMAGE_MODEL,
                image=image_file,
                prompt=(
                    "Edit the uploaded photo according to this request. "
                    "Preserve the main subject unless asked otherwise. User request: " + prompt
                ),
                size="1024x1024",
            )
        image_bytes = base64.b64decode(result.data[0].b64_json)
        await msg.reply_photo(photo=image_bytes, caption="୨୧ Фото готово! 🎀")
    except Exception:
        log.exception("Photo editing error")
        await msg.reply_text("Не удалось изменить фото. Проверь доступ к Image API и настройки.")
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


async def plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /cute текст, /generate описание или /help. 🎀")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cute", cute))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(
        MessageHandler(
            filters.PHOTO & filters.CaptionRegex(r"(?s)^/edit(?:@\w+)?(?:\s|$)"),
            edit_photo,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text))
    log.info("KawaiiPhotoBot is starting")
    app.run_polling()


if __name__ == "__main__":
    main()
