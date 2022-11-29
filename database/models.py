from sqlalchemy import Column, String, BigInteger

from .base import Base, engine


class PresentMessage(Base):
    __tablename__ = 'messages_for_present'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger)
    page_hash = Column(String(200), unique=True)
    channel_id = Column(BigInteger, nullable=True)
    bot_button_text = Column(String(200), nullable=True)
    bot_button_url = Column(String(200), nullable=True)
    present_message = Column(String(4000), nullable=True)
    presubscribe_message = Column(String(4000), nullable=True)


Base.metadata.create_all(engine)