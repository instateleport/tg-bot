import telebot
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
import random
from telebot import types

bot = telebot.TeleBot("5491920504:AAEEc9AnlStOtoYZATSJIfhOGJQM5R3Vvls")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    reply = "Ку"
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    global add_code
    add_code = str(random.randint(0, 9000000))
    markup.add(InlineKeyboardButton("Yes", switch_inline_query=add_code))

    bot.send_message(chat_id, text=reply, reply_markup=markup)


@bot.channel_post_handler(content_types='text')
def channel(message):
    print(message.text)
    print(message.chat.id)
    bot.delete_message(message.chat.id, message.id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(call)
    print(call.id)
    print(call.data)
    print(call.from_user.id)





bot.polling()