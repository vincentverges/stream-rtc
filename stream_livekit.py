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
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logging.info(
            "participant connected: %s %s", participant.sid, participant.identity)
    
    await room.connect(os.getenv('LIVEKIT_URL'), current_token)
    logging.info("connected to room %s", room.name)

if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    asyncio.run(app())
