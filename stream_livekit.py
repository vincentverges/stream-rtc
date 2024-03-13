import asyncio
import logging

from livekit import api, rtc
import os

current_token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')).with_identity("raspberry").with_name("Raspberry").with_grants(api.VideoGrants(
    room_join=True,
    room="rccar"
)).to_jwt()

print(current_token)

async def app():
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, current_token)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(app())
