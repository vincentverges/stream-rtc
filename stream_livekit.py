import asyncio
import logging

from livekit import api, rtc
import os

current_token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')).with_identity("raspberry").with_name("Raspberry").with_grants(api.VideoGrants(
    room_join=True,
    room="rccar"
)).to_jwt()

async def app():
    print("ICI")
    room = rtc.Room()
    print("LA")    
    await room.connect(os.getenv('LIVEKIT_URL'), current_token)
    print(room.name)

if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    asyncio.run(app())
