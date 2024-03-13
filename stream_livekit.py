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

    async def receive_frames(stream: rtc.VideoStream):
        async for frame in video_stream:
            # received a video frame from the track, process it here
            pass

    # track_subscribed is emitted whenever the local participant is subscribed to a new track
    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logging.info("track subscribed: %s", publication.sid)
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            video_stream = rtc.VideoStream(track)
            asyncio.ensure_future(receive_frames(video_stream))
    
    await room.connect(os.getenv('LIVEKIT_URL'), current_token)
    logging.info("connected to room %s", room.name)

    # participants and tracks that are already available in the room
    # participant_connected and track_published events will *not* be emitted for them
    for participant in room.participants.items():
        for publication in participant.tracks.items():
            print("track publication: %s", publication.sid)

if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    asyncio.run(app())
