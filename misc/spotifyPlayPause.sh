 #!/bin/bash

# This script sends the PlayPause command to Spotify.
# It fixes an issue with Spotify where it ignores when the PlayPause key is pressed.
# To make it work, intercept the pressing of the key from the OS settings (Ubuntu: Keyboard Settings > Custom Shortcuts)
# and execute this script whenever that event occurs.

 dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause