import asyncio
import logging
from signal import SIGINT, SIGTERM
from typing import Union
import os
import aiohttp
import json
import uuid
import time
import subprocess

from livekit import rtc

async def get_token():
    headers = {
        'identity': 'raspberry',  # Remplacez par l'identité souhaitée
        'name': 'Raspberry',  # Remplacez par le nom souhaité
        'room': 'rccar',  # Remplacez par le nom de la salle souhaité
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("http://165.22.203.182/token", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('token')
            else:
                logging.error(f"Failed to get token, status: {resp.status}")
                return None

async def publish_frame_to_livekit(room, process):
    # Envoi du stream sur la room
    # Créer une source vidéo personnalisée
    source = rtc.VideoSource(1920, 1080)
    # Créer une piste vidéo à partir de cette source
    track = rtc.LocalVideoTrack.create_video_track("camera", source)
    options = rtc.TrackPublishOptions()
    options.source = rtc.TrackSource.SOURCE_CAMERA
    publication = await room.local_participant.publish_track(track, options)
    logging.info("published track %s", publication.sid)
    asyncio.ensure_future(video_cycle(source, process))

 
async def video_cycle(source: rtc.VideoSource, process):
    while True: 
        raw_frame_data = await process.stdout.read(1920 * 1080 * 3)

        if not raw_frame_data:
            break

        video_frame = source.VideoFrame(width=1920, height=1080, data=raw_frame_data)
        source.capture_frame(video_frame)


async def start_ffmpeg_stream(video_pipe):
    # Commande pour capturer avec libcamera-vid et transcoder avec FFmpeg en H.264
    cmd = f"libcamera-vid -t 0 --width 1920 --height 1080 --framerate 30 --inline -o - | ffmpeg -i - -c:v libvpx -b:v 1M -f webm pipe:1 > {video_pipe}"
    # cmd = f"ffmpeg -f lavfi -i testsrc=size=1920x1080:rate=25 -c:v libvpx -b:v 1M -t 30 -f webm pipe:1 > {video_pipe}"
    process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return process

async def main(room: rtc.Room) -> None:

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        logging.info(
            "participant connected: %s %s", participant.sid, participant.identity
        )

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logging.info(
            "participant disconnected: %s %s", participant.sid, participant.identity
        )

    @room.on("local_track_published")
    def on_local_track_published(
        publication: rtc.LocalTrackPublication,
        track: Union[rtc.LocalAudioTrack, rtc.LocalVideoTrack],
    ):
        logging.info("local track published: %s", publication.sid)

    @room.on("active_speakers_changed")
    def on_active_speakers_changed(speakers: list[rtc.Participant]):
        logging.info("active speakers changed: %s", speakers)

    @room.on("local_track_unpublished")
    def on_local_track_unpublished(publication: rtc.LocalTrackPublication):
        logging.info("local track unpublished: %s", publication.sid)

    @room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logging.info(
            "track published: %s from participant %s (%s)",
            publication.sid,
            participant.sid,
            participant.identity,
        )

    @room.on("track_unpublished")
    def on_track_unpublished(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logging.info("track unpublished: %s", publication.sid)

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logging.info("track subscribed: %s", publication.sid)
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            _video_stream = rtc.VideoStream(track)
            # video_stream is an async iterator that yields VideoFrame
        elif track.kind == rtc.TrackKind.KIND_AUDIO:
            print("Subscribed to an Audio Track")
            _audio_stream = rtc.AudioStream(track)
            # audio_stream is an async iterator that yields AudioFrame

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logging.info("track unsubscribed: %s", publication.sid)

    @room.on("track_muted")
    def on_track_muted(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logging.info("track muted: %s", publication.sid)

    @room.on("track_unmuted")
    def on_track_unmuted(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logging.info("track unmuted: %s", publication.sid)

    @room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        logging.info("received data from %s: %s", data.participant.identity, data.data)

    @room.on("connection_quality_changed")
    def on_connection_quality_changed(
        participant: rtc.Participant, quality: rtc.ConnectionQuality
    ):
        logging.info("connection quality changed for %s", participant.identity)

    @room.on("track_subscription_failed")
    def on_track_subscription_failed(
        participant: rtc.RemoteParticipant, track_sid: str, error: str
    ):
        logging.info("track subscription failed: %s %s", participant.identity, error)

    @room.on("connection_state_changed")
    def on_connection_state_changed(state: rtc.ConnectionState):
        logging.info("connection state changed: %s", state)

    @room.on("connected")
    def on_connected() -> None:
        logging.info("connected")

    @room.on("disconnected")
    def on_disconnected() -> None:
        logging.info("disconnected")

    @room.on("reconnecting")
    def on_reconnecting() -> None:
        logging.info("reconnecting")

    @room.on("reconnected")
    def on_reconnected() -> None:
        logging.info("reconnected")

    token = await get_token()
    if token is None:
        logging.error("No token received, cannot connect to room.")
        return

    await room.connect(os.getenv('LIVEKIT_URL'), token)
    logging.info("connected to room %s", room.name)
    logging.info("participants: %s", room.participants)

    # Envoi d'un message dans le chat
    message_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)
    str_data = json.dumps({
        "id": message_id,
        "message": "C'est qui le patron ??!!",
        "timestamp": timestamp
        })
    data_to_send = str_data.encode()
    try:
        resp = await room.local_participant.publish_data(data_to_send, topic='lk-chat-topic')
        logging.info(f"Data sent succesfully : {resp} - {data_to_send}")
    except Exception as e:
        logging.error(f"Error sending data: {e}")


    # Flux video 
    video_pipe = "/tmp/video_pipe"

    # Créer un pipe nommé si nécessaire
    if not os.path.exists(video_pipe):
        os.mkfifo(video_pipe)

    # Démarrer la capture et le trascodage vidéo
    ffmpeg_task = await start_ffmpeg_stream(video_pipe)

    await publish_frame_to_livekit(room, ffmpeg_task)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler("basic_room.log"), logging.StreamHandler()],
    )

    loop = asyncio.get_event_loop()
    room = rtc.Room(loop = loop)

    async def cleanup():
        await room.disconnect()
        loop.stop()

    asyncio.ensure_future(main(room))
    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, lambda: asyncio.ensure_future(cleanup()))

    try:
        loop.run_forever()
    finally:
        loop.close()