import asyncio
import json
import websockets
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

class CameraStreamTrack(VideoStreamTrack):
	def __init__(self):
		super().__init__()
		# Utiliser ffmpeg pour capturer la video du Rasp
		self.player = MediaPlayer('/dev/media3', format='v4l2')
		
	async def recv(self):
		frame = await self.player.video.recv()
		return frame
		
async def connect_to_livekit(url, token):
	pc = RTCPeerConnection()
	pc.addTrack(CameraStreamTrack())
	
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
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTAyNDE3NDYsImlzcyI6IkFQSVJuaUthaFJaUUNIdSIsIm5iZiI6MTcxMDI0MDg0Niwic3ViIjoicmFzcGJlcnJ5IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6InJjY2FyIiwicm9vbUpvaW4iOnRydWV9fQ.Pa3RSRvXIklkq_Fkt52hIXyxxGWtTK9rWpBZnSL3yDk"

# Executer la fonction
asyncio.run(connect_to_livekit(LIVEKIT_URL, TOKEN))
