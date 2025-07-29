USERNAME=$(whoami)
mkdir "/home/$USERNAME/Project/"
sudo apt update
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtmultimedia
echo "Setup completed"
sudo mkdir /home/pi/.config/autostart
sudo cp /home/pi/Project/Ads.desktop  /home/pi/.config/autostart/