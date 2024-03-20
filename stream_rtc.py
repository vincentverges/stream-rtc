import subprocess

# Définit la commande pour capturer et transcoder le flux vidéo
command = "libcamera-vid -t 0 --width 1280 --height 720 --framerate 25 -o - | ffmpeg -i - -c:v libvpx -b:v 1M output_vp8.webm"

# Exécute la commande
subprocess.run(command, shell=True, check=True)