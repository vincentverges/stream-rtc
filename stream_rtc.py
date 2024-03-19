from picamera2 import Picamera2
import time


picamera2 = Picamera2()

video_config = picamera2.create_video_configuration(main={"size": (1920, 1080)})
picamera2.configure(video_config)

picamera2.start_preview()
time.sleep(20)
picamera2.stop_preview()