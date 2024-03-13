import asyncio
import logging
from picamera2 import Picamera2
from livekit import api, rtc

# Configuration de la caméra Raspberry Pi
WIDTH, HEIGHT = 1280, 720

# Informations LiveKit
LIVEKIT_URL = "wss://rccar-r1tndvld.livekit.cloud"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTAzMjk3ODEsImlzcyI6IkFQSVJuaUthaFJaUUNIdSIsIm5iZiI6MTcxMDMyODg4MSwic3ViIjoicmFzcGJlcnJ5IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6InJjY2FyIiwicm9vbUpvaW4iOnRydWV9fQ.InV-EFQVCd0_1SOoLWNQqfQiSM84iAxth9iFuf7fxB8"

class RaspberryPiCameraSource(rtc.VideoSource):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.picamera2 = Picamera2()
        self.preview_config = self.picamera2.create_preview_configuration(main={"size": (width, height)})
        self.picamera2.configure(self.preview_config)

    async def start_capture(self):
        self.picamera2.start()

    def capture_frame(self):
        # Capturez une frame de la caméra
        frame = self.picamera2.capture_array()
        return frame

async def publish_camera():
    # Créez une instance de Room
    room = rtc.Room()

    # Connectez-vous à la salle avec l'URL et le token
    await room.connect(LIVEKIT_URL, TOKEN)

    # Configurez la source vidéo Raspberry Pi
    camera_source = RaspberryPiCameraSource(WIDTH, HEIGHT)
    await camera_source.start_capture()

    # Créez et publiez la piste vidéo
    local_video_track = rtc.LocalVideoTrack.create_video_track("raspberry_cam", camera_source)
    await room.local_participant.publish_track(local_video_track)

    # Continuez à capturer et à envoyer des frames à LiveKit
    while True:
        frame = camera_source.capture_frame()
        local_video_track.send_frame(frame)
        await asyncio.sleep(1 / 30)  # Attendre pour correspondre à un framerate de 30 fps

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(publish_camera())
