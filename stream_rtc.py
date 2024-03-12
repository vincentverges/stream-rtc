import asyncio
import fractions
import numpy as np
import json
import websockets

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
		
async def connect_to_livekit(url, token):
	pc = RTCPeerConnection()
	relay = MediaRelay()
	
	local_video = GSTCameraStreamTrack()
	relayed_track = relay.subscribe(local_video)
	pc.addTrack(relayed_track)
	
	# Etablir une connexion WebSocket avec l'URL de LiveKit
	async with websockets.connect(url) as ws:
		# Envoyer le token pour l'auth
		await ws.send(json.dumps({'type':'join', 'token': token}))
		
		# Attendre la confirmation de LiveKit avant de continuer
		response = await ws.recv()
		print("Réponse de LiveKit: ", response)
		
		# Créer une offre WebRTC et l'envoyer à LiveKit via WebSocket
		offer = await pc.createOffer()
		await pc.setLocalDescription(offer)
		
		offer_msg = json.dumps({"type":"offer", "sdp": offer.sdp})
		await ws.send(offer_msg)
		
		# Attendre la reponse de LiveKit (Réponse WebRTC)
		answer_msg = await ws.recv()
		answer = json.loads(answer_msg)
		
		# Definir la description distante avec la réponse LiveKit
		if answer['type'] == 'answer':
			await pc.setRemoteDescription(RTCSessionDescription(type=answer['type'], sdp=answer['sdp']))
		else:
			print('Reponse innatendu de LiveKit: ', answer)
			

# URL et Token
LIVEKIT_URL = "wss://rccar-r1tndvld.livekit.cloud"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTAyODQxODMsImlzcyI6IkFQSVJuaUthaFJaUUNIdSIsIm5iZiI6MTcxMDI4MzI4Mywic3ViIjoicmFzcGJlcnJ5IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6InJjY2FyIiwicm9vbUpvaW4iOnRydWV9fQ.iGPvLXbbhg3CZUqU-ANvWsqPdCIRwdyIQIrdJsUQ6test7I"

# Executer la fonction
asyncio.run(connect_to_livekit(LIVEKIT_URL, TOKEN))
