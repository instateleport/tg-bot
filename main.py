import telebot
from telebot import types
import configparser
import random
import requests

# чтение конфигов
config_obj = configparser.ConfigParser()
config_obj.read("сonfigfile.ini", encoding='utf-8-sig')

token = config_obj["program_settings"]["token"]
bot_link = config_obj["program_settings"]["bot_link"]
bot_tag = "@" + bot_link.split("/")[-1]
print(bot_tag)
header_auth = config_obj["program_settings"]["header_auth"]
header_token = config_obj["program_settings"]["header_token"]

instructions_4_authors = config_obj["prewritten"]["instructions_4_authors"]
user_without_sub = config_obj["prewritten"]["user_without_sub"]
user_with_sub = config_obj["prewritten"]["user_with_sub"]


bot = telebot.TeleBot(token)
header = {header_auth: header_token}


def extract_start_code(text):
    # Extracts the start_code from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


def extract_uniqe_code(text):
    # Extracts the uniqe_code
    return text.split("_")[1]


def paid_and_gift(channel_id):
    # Here we should check subscription status
    r = requests.get('https://instateleport.ru/api/v1/telegram-page/present/' + channel_id,
                     headers=header)
    if r.status_code == 200:
        return r.json()["present_url"]
    else:
        return False


def link_generator(channel_id):
    return bot_link + '?start=user_' + str(channel_id)


def link_finder(channel_id):
    # Here we finding chanel associated with ID
    return bot.get_chat(channel_id).invite_link


def user_subscribed(chat_id, user_id):
    # Checking user sub
    try:
        bot.get_chat_member(chat_id, user_id)
        return True
    except telebot.apihelper.ApiTelegramException:
        return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    start_code = extract_start_code(message.text)
    reply = "unexpected error"
    markup = ''
    if start_code:  # if the '/start' command contains a start_code
        if "author" in start_code:
                reply = instructions_4_authors
                markup = types.InlineKeyboardMarkup()
                global add_code
                add_code = str(random.randint(0, 9000000))
                markup.add(types.InlineKeyboardButton("Добавить бота", switch_inline_query=str(add_code)+"_"+str(chat_id)))
        elif "user" in start_code:
            uniqe_code = str(extract_uniqe_code(start_code))
            print(uniqe_code)
            if paid_and_gift(uniqe_code):
                reply = user_with_sub + " " + link_finder(uniqe_code)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Я подписался", callback_data="user-subscribed_" + uniqe_code))
            else:
                reply = user_without_sub
    else:
        reply = "Please visit me via a provided URL from the website."
    bot.send_message(chat_id, text=reply, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    reply = ""
    if "user-subscribed" in call.data:
        channel_id = extract_uniqe_code(call.data)
        call_from_id = call.from_user.id
        call_from = call.from_user.username
        if user_subscribed(channel_id, call_from_id):
            gift = paid_and_gift(channel_id)
            if gift:
                requests.post(url='https://instateleport.ru/api/v1/telegram-page/subscriber/', headers=header, json={
                    "telegram_user_id": call_from_id,
                    "telegram_user_username": call_from,
                    "telegram_channel_id": channel_id
                })
                bot.send_message(call_from_id, "Вот твой подарок: " + gift)
            else:
                reply = "Произошла неизвестная ошибка"
        else:
            reply = "Ты не подписался на канал"
    bot.answer_callback_query(call.id, reply)


# Waiting
@bot.channel_post_handler(content_types='text')
def channel(message):
    global add_code
    if bot_tag in message.text:
        try:
            if add_code in message.text:
                del add_code
                chat_id = extract_uniqe_code(message.text.split()[1])
                print(chat_id)
                channel_id = message.chat.id
                link = link_generator(channel_id)
                bot.delete_message(channel_id, message.id)
                bot.send_message(chat_id, text="Вот твоя ссылка, вставь ее в кофигуратор " + link)
        except NameError:
            pass



bot.infinity_polling()
