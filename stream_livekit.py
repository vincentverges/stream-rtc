import asyncio
from livekit import rtc

# Informations LiveKit
LIVEKIT_URL = "wss://rccar-r1tndvld.livekit.cloud"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTAzMzk1MTYsImlzcyI6IkFQSVJuaUthaFJaUUNIdSIsIm5iZiI6MTcxMDMzODYxNiwic3ViIjoicmFzcGJlcnJ5IiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6InJjY2FyIiwicm9vbUpvaW4iOnRydWV9fQ.k7W-Ectl5SJ6hiDOpsOOYiKxjtuYc-vtGh3s-J63u8g"
API_KEY = "APIRniKahRZQCHu"
SECRET_KEY = "3L4tfzrYo7PbHYJuvX9HdGTwlzeAFNwJebpfiFOGMvfA"

async def app():
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, TOKEN)

if __name__ == "__main__":
    asyncio.run(app())
