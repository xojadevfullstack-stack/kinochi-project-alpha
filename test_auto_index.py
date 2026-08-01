import asyncio
import os
import sys

# Load env before any imports
from dotenv import load_dotenv
load_dotenv(os.path.abspath('backend/.env'))
load_dotenv(os.path.abspath('bot/.env'))

sys.path.insert(0, os.path.abspath('bot'))

from aiogram.types import Message, Chat, Document
from aiogram import Bot

class MockBot(Bot):
    def __init__(self):
        super().__init__(token="12345:mock")
        
    async def copy_message(self, chat_id, from_chat_id, message_id):
        class MockMsg:
            message_id = 9999
        return MockMsg()

class MockMessage(Message):
    def __init__(self, chat_id, thread_id):
        from datetime import datetime
        super().__init__(
            message_id=1000,
            date=datetime.now(),
            message_thread_id=thread_id,
            chat=Chat(id=chat_id, type="supergroup"),
            document=Document(
                file_id="mock_file_id_123",
                file_unique_id="mock_file_unique_id_123",
                mime_type="video/mp4"
            )
        )
        
    async def reply(self, text, **kwargs):
        print("BOT REPLIED:", text)

async def test():
    from handlers.auto_index import process_video
    
    bot = MockBot()
    msg = MockMessage(chat_id=-1003941035700, thread_id=405)
    print("Testing auto_index process_video...")
    
    await process_video(msg, bot)

if __name__ == "__main__":
    asyncio.run(test())
