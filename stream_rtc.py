import asyncio
import fractions
import numpy as np
import json
import websockets
import logging

from livekit import rtc
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialiser GStreamer
Gst.init(None)

class GSTCameraStreamTrack(VideoStreamTrack):
	"""
	Une piste vidéo qui reçoit des frames de GStreamer.
	"""
	
	def __init__(self):
		super().__init__()
		self.kind = "video"
		
		# Initialiser le pipeline GStreamer pour utiliser libcamera
		self.pipeline = Gst.parse_launch(
			"libcamerasrc ! video/x-raw,format=RGB,width=640,height=480,framerate=30/1 ! videoconvert ! appsink emit-signals=True name=appsink"
		)
		self.appsink = self.pipeline.get_by_name("appsink")
		self.appsink.connect("new-sample", self.on_new_sample)
		self.appsink.set_property("max-buffers", 1) # Garder uniquement la derniere frame
		self.appsink.set_property("drop", True) # Supprime les anciennes frames
		self.pipeline.set_state(Gst.State.PLAYING)
		
	def on_new_sample(self, appsink):
		sample = appsink.emit("pull-sample")
		if sample:
			buffer = sample.get_buffer()
			caps_format = sample.get_caps().get_structure(0)
			width = caps_format.get_value("width")
			height = caps_format.get_value("height")
			
			# Lire les données de la frame
			success, map_info = buffer.map(Gst.MapFlags.READ)
			if success:
				#créer un numpy array depuis les données de la frame
				frame_data = np.frombuffer(map_info.data, dtype=np.uint8)
				frame = frame_data.reshape((height, width, 3))
				buffer.unmap(map_info)
				
				# Injecter la frame dans aiortc
				# self.relay.track(self).add_frame(frame)
		
			return Gst.FlowReturn.OK

	async def recv(self):
		frame = await self.relay.track(self).recv()
		return frame

# URL et Token
URL = "wss://rccar-r1tndvld.livekit.cloud"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTAyOTExNjQsImlzcyI6IkFQSVJuaUthaFJaUUNIdSIsIm5iZiI6MTcxMDI5MDI2NCwic3ViIjoicmFzcGJlcnJ5IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6InJjY2FyIiwicm9vbUpvaW4iOnRydWV9fQ.yk4lXE_3pxXVgkQNLvuf54eBieXgTkbLPW1PLbG6mEA"

		
async def connect_to_livekit():
	room = rtc.Room()
	
	@room.on("participant_connected")
	def on_participant_connected(participant: rtc.RemoteParticipant):
		logging.info("Participant connecté:  %s %s",participant.sid, participant.idnetity)
		
	@room.on("track_subscribed")
	def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
		logging.info("Piste souscrite: %s", publication.sid)
		if isinstance(track, rtc.VideoTrack):
			asyncio.create_task(receive_frames(track))
			
	await room.connect(URL, TOKEN)
	logging.info("Connecté à la salle %s", room.name)
	

	local_video = GSTCameraStreamTrack()
	await room.local_participant.publish_video_track(track=local_video)

	while True:
		await asyncio.sleep(3600)
		
async def receive_frames(video_track):
	async for frame in video_track:
		pass
			

# Executer la fonction
if __name__=="__main__":
	logging.basicConfig(level=logging.INFO)
	asyncio.run(connect_to_livekit())
