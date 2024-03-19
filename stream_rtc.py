import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# Initialisation de GStreamer
Gst.init(None)

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        print("End-of-stream")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("Error: %s: %s" % (err, debug))
        loop.quit()
    return True

def main():
    # Création d'une boucle d'événements GMainLoop
    loop = GObject.MainLoop()

    # Création du pipeline GStreamer
    pipeline = Gst.parse_launch(
        "v4l2src device=/dev/video0 ! "  # Changez '/dev/video0' par votre périphérique vidéo
        "video/x-raw,width=640,height=480 ! "
        "videoconvert ! "
        "autovideosink"
    )

    # Ajout d'un gestionnaire pour les messages d'erreur sur le bus
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Lancement du pipeline
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Interrupted via CTRL+C")

    # Arrêt du pipeline et nettoyage
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()