print("🐾 StitchKitty запускается...")


import os
import telebot
print("📦 telebot импортирован!")

from telebot import types
from telebot.types import InputMediaPhoto


import json
import threading
import time
from datetime import datetime


from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Я жива! StitchKitty онлайн 🧵"

def run():
    app.run(host='0.0.0.0', port=9090)


# Запускаем веб-сервер в отдельном потоке
Thread(target=run).start()


TOKEN = '8053271515:AAGUFOJgQm7oosdX2tyRuomsAAGYm_Lk99U'
ADMIN_ID = 1235501707         # замени на свой Telegram ID
CHANNEL_ID = -1002298038944  # ID 

bot = telebot.TeleBot(TOKEN)

SP_DATA_FILE = "sp_data.json"
if not os.path.exists(SP_DATA_FILE):
    with open(SP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"active_sp": None, "participants": {}, "reports": []}, f)

def load_data():
    with open(SP_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(SP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

admin_states = {}

@bot.message_handler(commands=["создать_сп"])
def create_sp(message):
    if message.from_user.id != ADMIN_ID:
        return
    admin_states[message.from_user.id] = {"stage": "title"}
    bot.send_message(message.chat.id, "📌 Введи название СП:")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "title")
def get_title(message):
    admin_states[message.from_user.id]["title"] = message.text
    admin_states[message.from_user.id]["stage"] = "start_date"
    bot.send_message(message.chat.id, "📅 Введи дату начала (например, 01.06.2025):")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "start_date")
def get_start_date(message):
    admin_states[message.from_user.id]["start_date"] = message.text
    admin_states[message.from_user.id]["stage"] = "end_date"
    bot.send_message(message.chat.id, "📅 Введи дату окончания:")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "end_date")
def get_end_date(message):
    admin_states[message.from_user.id]["end_date"] = message.text
    admin_states[message.from_user.id]["stage"] = "description"
    bot.send_message(message.chat.id, "📝 Добавь комментарий к СП:")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "description")
def get_description(message):
    admin_states[message.from_user.id]["description"] = message.text
    admin_states[message.from_user.id]["stage"] = "start_codeword"
    bot.send_message(message.chat.id, "🔑 Введи кодовое слово для старта (одно):")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "start_codeword")
def get_start_codeword(message):
    admin_states[message.from_user.id]["start_codeword"] = message.text.strip()
    admin_states[message.from_user.id]["stage"] = "report_words"
    bot.send_message(message.chat.id, "🍓 Введи список кодовых слов для отчётов, через запятую:")

@bot.message_handler(func=lambda m: admin_states.get(m.from_user.id, {}).get("stage") == "report_words")
def get_report_words(message):
    words = [w.strip() for w in message.text.split(",") if w.strip()]
    if not words:
        bot.send_message(message.chat.id, "❗️Список не должен быть пустым. Введи слова через запятую.")
        return
    admin_states[message.from_user.id]["report_codewords"] = words
    admin_states[message.from_user.id]["stage"] = "logo"
    bot.send_message(message.chat.id, "📷 Пришли логотип СП (фото):")


InputMediaPhoto

user_states = {}
report_states = {}

@bot.message_handler(commands=["вступить_сп"])
def join_sp(message):
        user_id = str(message.from_user.id)
        data = load_data()

        if not data["active_sp"]:
            bot.send_message(message.chat.id, "⛔️ Сейчас нет активного СП.")
            return

        # Если регистрация была начата, но не завершена — сбросить состояние
        if user_id in user_states and user_id not in data["participants"]:
            del user_states[user_id]

            if user_id in data["participants"]:
                participant = data["participants"][user_id]
                if "start_photo" in participant and participant["start_photo"]:
                    bot.send_message(message.chat.id, "Ты уже участвуешь в этом СП! ❤️")
                    return
                else:
                    # регистрация была начата, но не завершена — удалим и разрешим снова
                    del data["participants"][user_id]
                    save_data(data)


        bot.send_message(message.chat.id, "👋 Как к тебе обращаться?")
        user_states[user_id] = {"stage": "name"}




@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id), {}).get("stage") == "name")
def get_name(m):
    user_id = str(m.from_user.id)
    name = m.text.strip()
    user_states[user_id]["name"] = name
    user_states[user_id]["stage"] = "start_photo"

    data = load_data()
    codeword = data["active_sp"]["start_codeword"]

    bot.send_message(m.chat.id, f"{name}, отлично! ✨\n"
                                f"🔑 Кодовое слово для старта: {codeword}\n"
                                f"📸 Теперь пришли, пожалуйста, фото для старта.")



@bot.message_handler(commands=["было"])
def start_report(message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data["participants"]:
        bot.send_message(message.chat.id, "Ты пока не участвуешь в СП. Напиши /вступить_сп 🌼")
        return

    report_states[user_id] = {"stage": "waiting_before"}
    bot.send_message(message.chat.id, "📸 Пришли фото \"Было\".")

@bot.message_handler(commands=["стало"])
def continue_report(message):
    user_id = str(message.from_user.id)
    if user_id not in report_states or report_states[user_id]["stage"] != "waiting_after":
        bot.send_message(message.chat.id, "Сначала пришли фото \"Было\" с помощью команды /было.")
        return
    bot.send_message(message.chat.id, "📸 Пришли фото \"Стало\".")

@bot.message_handler(content_types=["photo"])
def handle_photos(message):
    user_id = str(message.from_user.id)

    # стартовое фото
    if user_states.get(user_id, {}).get("stage") == "start_photo":
        data = load_data()
        file_id = message.photo[-1].file_id

        data["participants"][user_id] = {
            "name": user_states[user_id]["name"],
            "start_photo": file_id,
            "reports": []
        }
        save_data(data)
        del user_states[user_id]

        bot.send_message(message.chat.id, f"✨ Спасибо, {data['participants'][user_id]['name']}!\n"
      f"Ты успешно вступила в СП: *{data['active_sp']['title']}*.", parse_mode="Markdown")

        return

    # фото для "было/стало"
    if user_id in report_states:
        photo_id = message.photo[-1].file_id
        data = load_data()

        if report_states[user_id]["stage"] == "waiting_before":
            report_states[user_id]["before"] = photo_id
            report_states[user_id]["stage"] = "waiting_after"
            bot.send_message(message.chat.id, "✅ Фото \"Было\" получено. Теперь пришли фото \"Стало\" через /стало.")
        elif report_states[user_id]["stage"] == "waiting_after":
            report_states[user_id]["after"] = photo_id

            participant = data["participants"][user_id]
            active = data["active_sp"]

            report = {
                "user_id": user_id,
                "name": participant["name"],
                "before": report_states[user_id]["before"],
                "after": photo_id,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            data["reports"].append(report)
            participant["reports"].append(report["date"])
            save_data(data)

            bot.send_message(message.chat.id, f"📣 Отчёт от {participant['name']} по СП *{active['title']}*:", parse_mode="Markdown")
            media = [
                InputMediaPhoto(report["before"], caption="📍 Было"),
                InputMediaPhoto(report["after"], caption="✅ Стало")
            ]
            bot.send_media_group(message.chat.id, media)

            del report_states[user_id]


@bot.message_handler(commands=["статистика_сп"])
def send_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    if not data["active_sp"]:
        bot.send_message(message.chat.id, "Нет активного СП.")
        return

    title = data["active_sp"]["title"]
    text = f"📊 Статистика по СП *{title}*:\n\n"
    for uid, participant in data["participants"].items():
        name = participant["name"]
        reports = len(participant["reports"])
        text += f"🔹 {name} — {reports} отчётов\n"
    if not data["participants"]:
        text += "⛔️ Пока нет участниц."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["проверить_статус"])
def check_status(message):
    user_id = str(message.from_user.id)
    msg = f"🔎 Проверка ID {user_id}:\n"
    if user_id in user_states:
        msg += "📌 Есть в user_states\n"
    else:
        msg += "✔️ Нет в user_states\n"

    if user_id in report_states:
        msg += "📌 Есть в report_states\n"
    else:
        msg += "✔️ Нет в report_states\n"

    data = load_data()
    if user_id in data["participants"]:
        msg += "📌 Есть в participants\n"
    else:
        msg += "✔️ Нет в participants\n"

    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=["сбросить_регистрацию"])
def reset_registration(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗️Команду нужно отправить в ответ на сообщение участницы.")
        return

    user_id = str(message.reply_to_message.from_user.id)
    if user_id in user_states:
        del user_states[user_id]
        bot.send_message(message.chat.id, f"🗑 Регистрация пользователя {user_id} сброшена.")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден в user_states.")


def daily_check():
    while True:
        try:
            now = datetime.utcnow()
            if now.hour == 10 and now.minute == 0:  # 10:00 UTC → 13:00 МСК
                data = load_data()
                sp = data.get("active_sp")
                if not sp:
                    continue

                day = now.day
                if day in [14, 29]:
                    index = sp.get("report_index", 0)
                    words = sp.get("report_codewords", [])

                    if index < len(words):
                        code = words[index]
                        for uid, part in data["participants"].items():
                            try:
                                bot.send_message(uid, f"📣 {part['name']}, завтра отчётный день!\n"
                                                      f"🔑 Кодовое слово: *{code}*", parse_mode="Markdown")
                            except:
                                pass
                        sp["report_index"] += 1
                        save_data(data)
            time.sleep(60)
        except Exception as e:
            print("❗️ Ошибка в фоновом потоке:", e)
            time.sleep(60)

# запуск фоновой задачи
threading.Thread(target=daily_check, daemon=True).start()


print("StitchKitty СП запущен!")
bot.polling(none_stop=True)
