
if [ -f /etc/pacman.conf ]; then
  # Case of arch linux
  pacman -S python2 python2-gdata python2-oauth2client fswebcam
else
  # Case of ubuntu
  sudo apt-get install python python-gdata python-oauth2client fswebcam
fi

