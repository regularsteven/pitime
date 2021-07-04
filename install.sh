#run sudo sh install.sh 

echo "1 Running updates"
sudo apt-get update
echo "2 Running upgrades"
sudo apt-get upgrade
echo "-------------------------------------"
echo "3 Install hostapd"
sudo apt-get install hostapd
echo "4 Install hostapd"
sudo apt-get install dnsmasq
echo "5 Unmask and disable services"
sudo systemctl unmask hostapd

sudo systemctl disable hostapd
sudo systemctl disable dnsmasq
echo "6 Copy hostapd.conf"
sudo cp install/hostapd.conf /etc/hostapd/
echo "7 Updating /etc/default/hostapd"
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee -a /etc/default/hostapd
echo "8 Updating /etc/dnsmasq.conf"
echo '#AutoHotspot Config' | sudo tee -a /etc/dnsmasq.conf
echo '#stop DNSmasq from using resolv.conf' | sudo tee -a /etc/dnsmasq.conf
echo 'no-resolv' | sudo tee -a /etc/dnsmasq.conf
echo '#Interface to use' | sudo tee -a /etc/dnsmasq.conf
echo 'interface=wlan0' | sudo tee -a /etc/dnsmasq.conf
echo 'bind-interfaces' | sudo tee -a /etc/dnsmasq.conf
echo 'dhcp-range=10.0.0.50,10.0.0.150,12h' | sudo tee -a /etc/dnsmasq.conf
echo "-------------------------------------"
echo "9 Updating /etc/dnsmasq.conf"

echo 'nohook wpa_supplicant' | sudo tee -a /etc/dhcpcd.conf
echo "10 Copy autohotspot.service"
sudo cp install/autohotspot.service /etc/systemd/system/
echo "11 Starting autohotspot.service"
sudo systemctl enable autohotspot.service
echo "12 Copy autohotspot script"
sudo cp install/autohotspot /usr/bin/
echo "13 Make autohotspot script executable"
sudo chmod +x /usr/bin/autohotspot
echo "-------------------------------------"
echo "installing python dependencies"
sudo apt install python3-pip
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow

echo "Finished. On reboot, if no network is found, a hotspot will be created."