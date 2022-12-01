import os

from dotenv import dotenv_values


PROJECT_PATH = os.path.dirname(__file__)
PROJECT_DOTENV_PATH = os.path.join(PROJECT_PATH, '.env')

config = dotenv_values(PROJECT_DOTENV_PATH)
