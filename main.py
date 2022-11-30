import requests
import telebot
from telebot import types
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from config import config
from database.base import session
from database.models import PresentMessage


BOT_TOKEN = config['BOT_TOKEN']
BOT_URL = config['BOT_URL']
BOT_USERNAME = config['BOT_USERNAME']
HEADER_AUTH = config['HEADER_AUTH']
HEADER_JWT_TOKEN = config['HEADER_JWT_TOKEN']

INSTATELEPORT_API_BASE_URL = config['INSTATELEPORT_API_BASE_URL']

LINKING_CHANNEL_MESSAGE = config['LINKING_CHANNEL_MESSAGE']
PRESENT_NOT_FOUND_MESSAGE = config['PRESENT_NOT_FOUND_MESSAGE']

DEFAULT_HEADERS = {
    HEADER_AUTH: HEADER_JWT_TOKEN
}

bot = telebot.TeleBot(BOT_TOKEN)


def get_start_parameter(text, default=''):
    return text.split()[1] if len(text.split()) > 1 else default


def extract_page_hash_from_message(message):
    '''if visit this bot for linking channel to subscribe page'''
    return message.split('-')[1]


def extract_channel_id_from_message(message):
    '''if visit this bot via linked subscribe page'''
    return message.split('_')[1]


def generate_link_for_subscribe_page(channel_id):
    return f'{BOT_URL}?start=subscribe-page_{channel_id}'


def find_invite_link(channel_id):
    # Here we finding chanel associated with ID
    return bot.get_chat(channel_id).invite_link


def user_subscribed(chat_id, user_id):
    # Checking user sub
    try:
        print(bot.get_chat_member(chat_id, user_id))
        if bot.get_chat_member(chat_id, user_id).status != 'left':
            return True
    except telebot.apihelper.ApiTelegramException:
        print('error')
        pass
    print('no')
    return False


def generate_channel_username(message):
    print(message)
    channel_username = ''
    try:
        return message.chat.username
    except KeyError:
        pass
    try:
        channel_username += message.chat.first_name
    except KeyError:
        pass
    try:
        channel_username += ' ' + message.chat.last_name
    except KeyError:
        pass
    return channel_username


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    start_parameter = get_start_parameter(message.text)
    reply = 'unexpected error'
    markup = ''
    if 'subscribe-page' in start_parameter:
        channel_id = extract_channel_id_from_message(start_parameter)
        present_message = session.scalar(
            select(PresentMessage).where(PresentMessage.channel_id == channel_id)
        )
        if present_message:
            reply = present_message.presubscribe_message + ' ' + find_invite_link(channel_id)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Я подписался', callback_data=f'user-subscribed_{channel_id}'))
        else:
            reply = PRESENT_NOT_FOUND_MESSAGE
    else:
        try:
            session.execute(
                insert(PresentMessage).values(
                    page_hash=start_parameter,
                    chat_id=chat_id
                )
            )
        except IntegrityError:
            print('IntegrityError')
        finally:
            session.commit()
        reply = LINKING_CHANNEL_MESSAGE
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Подключить канал', switch_inline_query=f'{chat_id}-{start_parameter}'))
    bot.send_message(chat_id, text=reply, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    reply = None
    if 'user-subscribed' in call.data:
        channel_id = extract_channel_id_from_message(call.data)
        call_from_id = call.from_user.id
        if user_subscribed(channel_id, call_from_id):
            present_message = session.scalar(
                select(PresentMessage).where(PresentMessage.channel_id == channel_id)
            )
            if present_message:
                bot.send_message(
                    call_from_id,
                    present_message.present_message + f'\n<a href="{present_message.bot_button_url}">{present_message.bot_button_text}</a>',
                    parse_mode='html'
                )
            else:
                reply = 'Произошла неизвестная ошибка'
        else:
            reply = 'Ты не подписался на канал'
    bot.answer_callback_query(call.id, reply)


@bot.channel_post_handler(content_types='text')
def channel_has_message_for_linking_subscribe_page_handler(message):
    page_hash = extract_page_hash_from_message(message.text)
    print(f'{page_hash=}')
    chat_id = session.scalar(
        select(PresentMessage).where(PresentMessage.page_hash == page_hash)
    ).chat_id
    print(f'{chat_id=}')

    if (BOT_USERNAME in message.text) and (str(chat_id) in message.text) and (page_hash in message.text):
        channel_id = message.chat.id
        telegram_bot_url = generate_link_for_subscribe_page(channel_id)
        bot.delete_message(channel_id, message.id)

        response = requests.put(
            f'{INSTATELEPORT_API_BASE_URL}link-telegram/',
            headers=DEFAULT_HEADERS,
            json={
                'telegram_username': generate_channel_username(message),
                'page_hash': page_hash,
                'telegram_bot_url': telegram_bot_url
            }
        )
        response_json = response.json()
        print(response_json)
        session.execute(
            update(PresentMessage).where(
                PresentMessage.page_hash == page_hash
            ).values(
                channel_id=channel_id,
                bot_button_text=response_json['bot_button_text'],
                bot_button_url=response_json['bot_button_url'],
                present_message=response_json['present_message'],
                presubscribe_message=response_json['presubscribe_message'],
            )
        )
        session.commit()
        bot.send_message(chat_id, text='Канал успешно привязан')


if __name__ == '__main__':
    bot.infinity_polling()
