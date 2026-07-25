import redis.asyncio as redis
import asyncio

async def main():
    r = redis.from_url('rediss://certain-aphid-84911.upstash.io:6379')
    try:
        await r.ping()
        print("Connected!")
    except Exception as e:
        print(repr(e))

asyncio.run(main())
