import requests

from config import config


class TeleportAPI:
    def __init__(self, auth_token: str, auth_header: str) -> None:
        self.__DEFAULT_REQUEST_HEADERS = {
            auth_header: auth_token
        }
        self.__TELEPORT_API_BASE_URL = config['INSTATELEPORT_API_BASE_URL']

    def patch_api_request(self, url: str, json: dict) -> dict:
        if url[-1] != '/':
            url += '/'

        response = requests.patch(
            f'{self.__TELEPORT_API_BASE_URL}{url}',
            headers=self.__DEFAULT_REQUEST_HEADERS,
            json=json
        )
        return response.json()

    def update_subscribers_count(self, page_hash: str, chat_id: int, channel_id: int) -> dict:
        response = self.patch_api_request(
            url='update-subscribe-telegram-page-statistic/',
            json={
                'page_hash': page_hash,
                'chat_id': chat_id,
                'channel_id': channel_id
            }
        )
        return response

    def link_subscribe_telegram_page(self, channel_username: str, page_hash: str, telegram_bot_url: str) -> dict:
        response = self.patch_api_request(
            url='link-subscribe-telegram-page/',
            json={
                'telegram_username': channel_username,
                'page_hash': page_hash,
                'telegram_bot_url': telegram_bot_url
            }
        )
        return response
