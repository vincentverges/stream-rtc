import subprocess

# Définit la commande pour capturer et transcoder le flux vidéo
command = "libcamera-vid -t 0 --width 1920 --height 1080 --framerate 25 --inline --listen -o - | ffmpeg -i - -c:v copy output_h264.mp4"

# Exécute la commande
subprocess.run(command, shell=True, check=True)