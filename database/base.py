from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import config


POSTGRES_DB_NAME = config['POSTGRES_DB_NAME']
POSTGRES_DB_HOST = config['POSTGRES_DB_HOST']
POSTGRES_USER_USERNAME = config['POSTGRES_USER_USERNAME']
POSTGRES_USER_PASSWORD = config['POSTGRES_USER_PASSWORD']

engine = create_engine(f'postgresql+psycopg2://{POSTGRES_USER_USERNAME}:{POSTGRES_USER_PASSWORD}@{POSTGRES_DB_HOST}/{POSTGRES_DB_NAME}')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()