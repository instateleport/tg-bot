import requests
import configparser
config_obj = configparser.ConfigParser()
config_obj.read("сonfigfile.ini", encoding='utf-8-sig')
header_auth = config_obj["program_settings"]["header_auth"]
header_token = config_obj["program_settings"]["header_token"]
header = {header_auth: header_token}


r = requests.get('https://instateleport.ru/api/v1/telegram-page/present/some_channell_id',
                 headers=header)

call_from_id = 111222333
call_from = "testUsername"
channel_id = -1001814440518
d = requests.post(url='https://instateleport.ru/api/v1/telegram-page/subscriber/', headers=header, json={
                    "telegram_user_id": call_from_id,
                    "telegram_user_username": call_from,
                    "telegram_channel_id": channel_id
                })

print(r)
print(r.json()["present_url"])

print(d)