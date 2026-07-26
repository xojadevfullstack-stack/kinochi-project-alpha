import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('bot'))

async def test_sender():
    from bot.utils.movie_sender import send_movie_to_user

    class AsyncMock:
        def __init__(self):
            self.mock_calls = []
        async def send_video(self, **kwargs):
            self.mock_calls.append(("send_video", kwargs))
        async def send_message(self, **kwargs):
            self.mock_calls.append(("send_message", kwargs))
        async def copy_message(self, **kwargs):
            self.mock_calls.append(("copy_message", kwargs))

    bot = AsyncMock()
    movie = {
        "title": "Test Movie",
        "code": "12345678",
        "translations": [
            {
                "id": 1,
                "language": "Asosiy",
                "telegram_file_id": "file123",
                "storage_channel_message_id": 100
            }
        ]
    }
    
    success = await send_movie_to_user(bot, 1234, movie)
    print("Success:", success)
    print("Bot mock calls:", bot.mock_calls)

if __name__ == "__main__":
    asyncio.run(test_sender())
