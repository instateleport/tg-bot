import telebot
from telebot import types
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from config import config
from logger import logger
from teleport_api import TeleportAPI
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

bot = telebot.TeleBot(BOT_TOKEN)
teleport_api = TeleportAPI(
    auth_token=HEADER_JWT_TOKEN,
    auth_header=HEADER_AUTH
)


def get_start_parameter(text, default=''):
    return text.split()[1] if len(text.split()) > 1 else default


def extract_page_hash_from_message(message):
    '''if visit this bot for linking channel to subscribe page'''
    return message.split('-')[1]


def extract_channel_id_from_message(message):
    '''if visit this bot via linked subscribe page'''
    return message.split('_')[1]


def extract_page_hash_from_get_present_message(message):
    '''if visit this bot via linked subscribe page'''
    return message.split('_')[2]


def generate_link_for_subscribe_page(channel_id, page_hash):
    return f'{BOT_URL}?start=subscribe-page_{channel_id}_{page_hash}'


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
    return message.chat.title


@logger.catch
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    logger.info(f'начинается взаимодействие с пользователем {chat_id=}')

    start_parameter = get_start_parameter(message.text)
    reply = 'unexpected error'
    markup = ''
    if 'subscribe-page' in start_parameter:
        logger.info('этот пользователь хочет получить подарок')
        channel_id = extract_channel_id_from_message(start_parameter)
        page_hash = extract_page_hash_from_get_present_message(start_parameter)
        present_message = session.scalar(
            select(PresentMessage).where(PresentMessage.page_hash == page_hash)
        )
        if present_message:
            reply = present_message.presubscribe_message + ' ' + find_invite_link(channel_id)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Я подписался', callback_data=f'user-subscribed_{channel_id}_{page_hash}'))
        else:
            reply = PRESENT_NOT_FOUND_MESSAGE
    else:
        logger.info('этот пользователь хочет привязать страницу')
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

        logger.debug(f'сообщение для привязки есть {chat_id}-{start_parameter}')

        markup.add(types.InlineKeyboardButton('Подключить канал', switch_inline_query=f'{chat_id}-{start_parameter}'))
    bot.send_message(chat_id, text=reply, reply_markup=markup)


@logger.catch
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    reply = None
    if 'user-subscribed' in call.data:
        channel_id = extract_channel_id_from_message(call.data)
        page_hash = extract_page_hash_from_get_present_message(call.data)
        call_from_id = call.from_user.id
        if user_subscribed(channel_id, call_from_id):
            present_message = session.scalar(
                select(PresentMessage).where(PresentMessage.page_hash == page_hash)
            )
            teleport_api.update_subscribers_count(
                page_hash=present_message.page_hash,
                chat_id=call_from_id,
                channel_id=channel_id
            )
            if present_message:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(present_message.bot_button_text, url=present_message.bot_button_url))
                bot.send_message(
                    call_from_id,
                    present_message.present_message,
                    reply_markup=markup
                )
            else:
                reply = 'Произошла неизвестная ошибка'
        else:
            reply = 'Ты не подписался на канал'
    bot.answer_callback_query(call.id, reply)


@logger.catch
@bot.channel_post_handler(content_types='text')
def channel_has_message_for_linking_subscribe_page_handler(message):
    reply = 'Канал успешно привязан'
    channel_username = generate_channel_username(message)
    page_hash = extract_page_hash_from_message(message.text)
    logger.info(f'начинается привязка подписной страницы {page_hash} к каналу {channel_username}')

    chat_id = session.scalar(
        select(PresentMessage).where(PresentMessage.page_hash == page_hash)
    ).chat_id
    logger.debug(f'пользователь этого канала имеет {chat_id=}')

    if (BOT_USERNAME in message.text) and (str(chat_id) in message.text) and (page_hash in message.text):
        channel_id = message.chat.id
        telegram_bot_url = generate_link_for_subscribe_page(channel_id, page_hash)
        bot.delete_message(channel_id, message.id)

        response = teleport_api.link_subscribe_telegram_page(
            channel_username=channel_username,
            page_hash=page_hash,
            telegram_bot_url=telegram_bot_url
        )
        logger.info(f'ответ вызова привязки подписной страницы: {response}')

        if 'error' in response:
            reply = response['error']
        else:
            session.execute(
                update(PresentMessage).where(
                    PresentMessage.page_hash == page_hash
                ).values(
                    channel_id=channel_id,
                    bot_button_text=response['bot_button_text'],
                    bot_button_url=response['bot_button_url'],
                    present_message=response['present_message'],
                    presubscribe_message=response['presubscribe_message'],
                )
            )
            session.commit()
        bot.send_message(chat_id, text=reply)


if __name__ == '__main__':
    bot.infinity_polling()
