# letslapse
raspberry pi timelaps rig

# configure device
1) install raspbian
2) add wpa_supplicant.conf and 'ssh' files to boot root directory
 > ssh pi@raspberry.local / password raspberry
 > in some instances, this will fail if previously ssh'd to a same name or IP
 > edit C:\Users\user-name\.ssh on windows / "ssh-keygen -R raspberrypi.local" on ubuntu
 > remove the raspberrypi.local line, save and SSH again
 > can find devices on network across IPs of devices on linux with nmap -sP 192.168.88.0/24
   > Additional ideas at https://raspberrypi.stackexchange.com/questions/13936/find-raspberry-pi-address-on-local-network
   > nmap -sP 192.168.215.0/24 | awk '/^Nmap/{ip=$NF}/B8:27:EB/{print ip}'
   > arp -na | grep -i b8:27:eb
   > FOR Pi4B, need to search for dc:a6:32 MAC ID, eg arp -na | grep -i dc:a6:32
3) update user password / system
 > passwd
 > sudo apt update
 > sudo apt upgrade
4) enable the camera / change the device name if we wish
 > sudo raspi-config
 > interface > Camera
5) install git / tools / apache webserver (or other) to allow for simple view / management of debug and testing tools
 > sudo apt install git -y
 > sudo apt install apache2 -y (option)
 > sudo apt remove php libapache2-mod-php -y (option)
 > sudo apt install python3-pip -y
6) boot and ssh, clone https://github.com/regularsteven/letslapse into /var/www/html (if basic apache)
 > git clone https://github.com/regularsteven/letslapse.git
 > need to remove everything inside the folder if installing to apache (sudo rm -R /var/www/html/*)
 > OR install whereever
7) Python and dependencies
 > sudo apt install python3-pip
 > python3 -m pip install --upgrade pip
 > python3 -m pip install --upgrade Pillow
 > python3 -m pip install --upgrade Pillow --global-option="build_ext" --global-option="--enable-[feature]"
 > sudo apt install libopenjp2-7 libopenjp2-7-dev libopenjp2-tools

 On device, to run blend scripts:
    sudo pip3 install opencv
    sudo apt-get install libatlas-base-dev
    sudo pip3 install piexif


8) Enable PYTHON server to start on system boot
 > enable CONSOLE AUTO login via sudo raspi-config (SYSTEM OPTIONS > BOOT)
 > make the script executable: sudo chmod +x /home/pi/letslapse/server.py
 > add sudo python /home/pi/letslapse/server.py at the bottom of sudo nano /etc/profile

9) Install SAMBA for simple filesystem access
    sudo apt-get install samba samba-common-bin 
    # sudo apt-get remove samba samba-common-bin
    sudo nano /etc/samba/smb.conf
    * add to the bottom:
            [pimylifeupshare]
        path = /home/pi/shared
        writeable=Yes
        create mask=0777
        directory mask=0777
        public=no
    sudo smbpasswd -a pi
    sudo systemctl restart smbd 

10) Mounting for remote access of files with another pi
 > sudo mkdir /media/share 
 > nano /home/pi/.smbcredentials 
    - username=smb_username
    - password=smb_password
 > sudo mount -t cifs -o rw,vers=3.0,credentials=/home/pi/.smbcredentials //pi.local/letslapse /media/sharePi
 > sudo mount -t cifs -o rw,vers=3.0,credentials=/home/pi/.smbcredentials_pi //pi.local/letslapse /media/sharePi
 > sudo nano /etc/fstab 
   - to reconnect on reboot, add //pi.local/letslapse /media/sharePi cifs _netdev,vers=3.0,credentials=/home/pi/.smbcredentials,uid=pi,gid=pi,x-systemd.automount 0 0

11) Auto backup to second (non-shooting) pi device (my device is USB called letslapsepics / msdos FAT)
 > make director sudo mkdir /media/usb
 > sudo mount /dev/sda1 /media/usb
  - if unsure of /dev/name, run sudo fdisk -l
  - if FAT, need to run sudo mount -t vfat /dev/sda1 /media/usb -o uid=1000,gid=1000,utf8,dmask=027,fmask=137
 AUTO Mount on BOOT
 > sudo pico /etc/fstab
  > get UUID with sudo blkid
  add: UUID=088E-FCEF /media/usb auto nosuid,nodev,nofail 0 0
  > cp group1 /media/usb -r --verbose -n
  > rsync from remote to loca
   -- sudo rsync -h -v -r -P -t /media/sharePi/auto/ /media/usb/ --ignore-existing
    ## copy on ubuntu system
    ### mount the drive and open the remote SMB share in terminal
    ### ensure the folder exists inside /mnt/ssd/Clients/PiShots/original/ + name    
    rsync -h -v -r -P -t * /mnt/ssd/Clients/PiShots/originals/auto-monitor-knocked/ --ignore-existing
   

   sudo crontab -e
   @reboot sudo rsync -h -v -r -P -t /media/sharePi/auto/ /media/usb/ 


## POWER REDUCTION

# remove bluetooth
sudo pico /boot/config.txt

Add below, save and close the file Permalink
#Disable Bluetooth
dtoverlay=disable-bt

#or remove everything
sudo apt-get purge bluez -y
sudo apt-get autoremove -y

# kill LED light on zero

echo none | sudo tee /sys/class/leds/led0/trigger
echo 1 | sudo tee /sys/class/leds/led0/brightness

Add the following sudo pico /boot/config.txt
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on


#disable hdmi
/usr/bin/tvservice -o
sudo pico /etc/rc.local
 > add /usr/bin/tvservice -o


# running app in python
1) capture images

2) convert group of images by timeframe (i.e. 60 seconds) to timelapse
python3 ../longexposure.py --groupBy 60 --groupByType seconds --makeMP4 yes


shoot, edit, stream

"local internal" = internal storage
"local storage" = SD or HDD storage

## to do
1) capture image - at interval
    from pi hq camera
    or from sony (gphoto2)
    or from fake source (i.e. folder one by one)
    &
    place image inside 'drop' local storage folder if available
        - else wait until it's back (might have been disconnected for transfer to backup / delete)
2) watch 'drop' folder for new files
    extract JPEG if possible (exiftool)
    or create JPEG if not possible
    & 
    extract to 'processed' local storage folder
3a) Option A - Simple Local Stream (ffmpeg)
    processed folder sorts by most recent

    //options:
    ffmpeg -loop 1 -i BangkokSky-%d.jpg -vf scale=320:240 -r 10 -vcodec mpeg4 -f mpegts udp://127.0.0.1:554

    resize: 
    ffmpeg -loop 1 -i BangkokSky-%d.jpg -vf scale=320:240 -r .5 -vcodec mpeg4 -f mpegts udp://192.168.30.75:9099

   test stream:
   ffprobe udp://192.168.30.75:9099

    ffmpeg -loop 1 -re -f lavfi -i BangkokSky-%d.jpg -vf scale=320:240 -r .5 -f rtp rtp://192.168.56.75:9099




    ffmpeg -y -i rtsp://admin:admin@192.168.56.75:554/live -vframes 1 BangkokSky-1.jpg


    # local video - is working: 
    ## ffmpeg -i melbourne.mp4 -f mpegts udp://127.0.0.1:9099
    ## open in vlc: udp://@127.0.0.1:9099
    ## ffmpeg -i melbourne.mp4 -f mpegts udp://192.168.30.75:9099
    ## open local: udp://@192.168.30.75:9099

    #local image -  is working:
    ##ffmpeg -loop 1 -i BangkokSky-%d.jpg -vf scale=320:240 -r .5 -vcodec mpeg4 -f mpegts udp://192.168.30.75:9099
    ## open local udp://@192.168.30.75:9099

    //ffmpeg -i melbourne.mp4 -f rtp rtp://192.168.30.75:9099
    //ffmpeg -i melbourne.mp4 -vf scale=320:240 -r .5 -f rtp rtp://192.168.30.75:9099



    # resize all images - is working
    ## ffmpeg -i BangkokSky-%d.jpg -vf scale="720:-1" resize%d.jpg


    1: Get full image
    2: convert image to small version
        - ffmpeg -i BangkokSky-%d.jpg -vf scale="720:-1" resize/seq%d.jpg
    3: update the stream with the smaller versions
        - ffmpeg -loop 1 -i seq%d.jpg  -r .5 -vcodec mpeg4 -f mpegts udp://192.168.30.75:9099


    update camera for libcamera use - could eb a better option for low light / blue hour usage

# ffmpeg resize 
ffmpeg -i seq_%04d.jpg -vf scale=1920:-1 resize/small_%04d.jpg

# ffmpeg create timelapse seq 
ffmpeg -framerate 25 -pattern_type glob -i "*.jpg" -c:v libx264 -crf 0 output.mp4  -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"
ffmpeg -r 24 -i small_%04d.jpg -vcodec libx264 -y -an video.mp4 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"

streaming idea 2: WORKING across network
raspivid -t 0 -l -o tcp://192.168.1.11:3333 -w 640 -h 360
raspivid -t 0 -l -o tcp://192.168.1.11:3333 -w 1280 -h 720
raspivid -t 0 -l -o tcp://pi.local:3333 -w 1280 -h 720
vlc tcp/h264://192.168.1.11:3333
OR
tcp/h264://192.168.30.76:3333


MJPEG Stream
https://desertbot.io/blog/how-to-stream-the-picamera - works but requires its own dependencies




IDEA

1) display most recent low-res image as poster frame in html img src
    Javascript to refresh to the image every minute
2) behind this image, previous images and load up slider for scrobble player


3) Take photos in alternative sequence - compare results
    > A - Manual Settings, as defined by Steve
    > B - Full AUTO, as captured by sensor



3b) 


# troubleshooting
sometimes the camera crashes - find it and kill it
ps -A | grep raspi
sudo kill 1599 


# pillow for image analysis
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow

not required, but in docs:


# for opencv and image processing
python3 -m pip install --upgrade imutils
python3 -m pip3 install opencv-contrib-python
python3 -m pip install opencv-python - this worked, not contrib version
python3 -m pip install numpy
python3 -m pip install picamera



# batching images for fake long exposures
longexposure.py requires import os, numpy, PIL
    > basically smashes all files in folder to one image
    > need to batch this up in minute by minute / or 30 second blocks

# deflicker
Attempt 1: Not good enough with current flicker during sunset
http://joegiampaoli.blogspot.com/2015/04/creating-time-lapse-videos-mostly-in.html
 > requires PERL
 > apt-get install libfile-type-perl libterm-progressbar-perl perlmagick libimage-exiftool-perl
 > chmod +x timelapse-deflicker.pl

Attempt 2:
https://pypi.org/project/deflicker/
 > running this against output from attemt 2 as first shot - 
 > 





 Observations
 Using "raspistill -t 1 --ISO "+str(ISO)+" -ex verylong -w 4000 -h 3000"
  > Day light / high light: 10 to 12 images per 60 seconds (at 1/2315 sec or so - i.e. very fast exposure ISO 10)
  > Night light / low light: 1 image per 60 seconds (at 7 sec i.e. 800)


  Using "raspistill -t 1 -bm -ag 1 --ISO "+str(ISO)+" -awb off -awbg 3,2 -co -10 -ex verylong  -w 2400 -h 1800"
  > Day light : 16 images per 60 second block
  > Night light : 1 ... hmmmm


  12Mp images
   Start: Tue, 25 May 2021  06:32:38
   Image 100: 06:42:26
   Image 200: 06:54:55

   200 images = 1.2GB over 20 minutes
   3.6GB images per hour
   43Gb per 12 hours at 200 images per hour at high light
   Much less for over night.... 


# setting up Pi as HOTSPOT to host server / be the network
1) update and upgrade
sudo apt-get update
sudo apt-get upgrade
2) install the following:
sudo apt-get install dnsmasq hostapd
3) We need to configure the new services, so kill them for now
sudo systemctl stop dnsmasq
sudo systemctl stop hostapd
4) Configure static and IP ranges
sudo nano /etc/dhcpcd.conf
 - add the following at the end
interface wlan0
static ip_address=10.0.0.1/24
nohook wpa_supplicant

6) configure DHCP server
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig

sudo nano /etc/dnsmasq.conf
 - add the following

interface=wlan0 # Use the require wireless interface - usually wlan0
dhcp-range=10.0.0.2,10.0.0.20,255.255.255.0,24h

7) Configuring the Access Point Host Software (hostapd)
sudo nano /etc/hostapd/hostapd.conf
 - add the following

interface=wlan0
driver=nl80211
ssid=LetsLapse
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=Together
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

8) 
sudo service dhcpcd restart

sudo rfkill unblock wifi
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd


10) restart services
sudo service dhcpcd restart







# making changes to exposure / gains
--------------
a few variables are in place to help maintain consistency of the shoot

in some instances, the camera captured back images with no explanation - in this example, the output brightnessPerceived score was low
brightnessPerceived score: 35.96887358252723

When this happens, or the brightnessPerceived is below 50, the images taken right after shouldn't be brightened up as it's a dud image - without the brightnessChangeOfSignificance toggle, this would blow out (overexpose) following images

----------------
gains for blue and red are more complicated

raspistill -t 1 -bm -ag 1 -sa -10 -dg 1.0 -ag 1.0 -awb off -awbg 1.7913023058720001,1.64491119408 -co -15 -ex off -w 4056 -h 3042 -ss 22589.645963694675 -o auto_default/group1/image1614.jpg
brightnessPerceived score: 120.56416323374215
auto-measured gains: 1.921875, 1.48828125
awbgSettings: 1.7913023058720001,1.64491119408
-----------------------------------------
raspistill -t 1 -bm -ag 1 -sa -10 -dg 1.0 -ag 1.0 -awb off -awbg 1.7913023058720001,1.64491119408 -co -15 -ex off -w 4056 -h 3042 -ss 22589.645963694675 -o auto_default/group1/image1615.jpg
brightnessPerceived score: 123.46989174755981
auto-measured gains: 1.90234375, 1.4921875
awbgSettings: 1.7913023058720001,1.64491119408
-----------------------------------------
raspistill -t 1 -bm -ag 1 -sa -10 -dg 1.0 -ag 1.0 -awb off -awbg 1.7913023058720001,1.64491119408 -co -15 -ex off -w 4056 -h 3042 -ss 22589.645963694675 -o auto_default/group1/image1616.jpg
brightnessPerceived score: 120.47623420011236
auto-measured gains: 1.90234375, 1.4921875
awbgSettings: 1.7913023058720001,1.64491119408




# test shots
raspistill -t 1 --ISO 800 -co -15 -ex off -w 2400 -h 1800.0 -ss 147110.21692236557 --latest latest.jpg -o test.jpg -bm -ag 1 -sa -10 -awb off -awbg 3.484375,1.44921875 -co -15 -ex off 

# test shoots for faster captures in low light
raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex off -ss 10000000 -dg 8 -o toilet-dg8_ss10000000.jpg

 > takes 21 seconds

raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex off -ss 20000000 -dg 12 -o toilet_dg12_ss_20000000.jpg

 > takes 42
 > good brightness

 raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex off -ss 20000000 --ISO 800 -o toilet_iso800_ss_20000000.jpg

  > takes 42
  > too dark
  > iso marked as 6


 raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex night -ss 20000000 --ISO 800 -o toilet-iso800-ss20000000-ex_night.jpg

  > takes 2:22 (140 seconds | 7x on capture time)
  > iso marked as 800
  > similar results as dg12 20 seconds

raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex off -ss 20000000 -dg 12 -ag 8 -o toilet2_dg12_ag8_ss_20000000.jpg
  > Crazy overexpose


raspistill -t 1 -w 2400 -h 1800 -awb off -awbg 3.484375,1.44921875 -ex off -ss 20000000 -dg 12 -ag 2 -o toilet2_dg12_ag2_ss_20000000.jpg
  
# issues with performance
 > https://www.raspberrypi.org/blog/sd-card-speed-test/
  > cd /usr/share/agnostics/
  > sudo sh /usr/share/agnostics/sdtest.sh




# SD Card Speed tests
test 1 - 256GB Card
Run 1
seq-write;0;0;10244;20
rand-4k-write;0;0;1730;432
rand-4k-read;6674;1668;0;0
Sequential write speed 10244 KB/sec (target 10000) - PASS
Random write speed 432 IOPS (target 500) - FAIL
Random read speed 1668 IOPS (target 1500) - PASS
Run 2
prepare-file;0;0;9999;19
seq-write;0;0;9863;19
rand-4k-write;0;0;1763;440
rand-4k-read;6565;1641;0;0
Sequential write speed 9863 KB/sec (target 10000) - FAIL
Note that sequential write speed declines over time as a card is used - your card may require reformatting
Random write speed 440 IOPS (target 500) - FAIL
Random read speed 1641 IOPS (target 1500) - PASS
Run 3
prepare-file;0;0;10556;20
seq-write;0;0;10366;20
rand-4k-write;0;0;1748;437
rand-4k-read;6459;1614;0;0
Sequential write speed 10366 KB/sec (target 10000) - PASS
Random write speed 437 IOPS (target 500) - FAIL
Random read speed 1614 IOPS (target 1500) - PASS




# stripping back raspbian for ligher use
aplay - remove
pulseaudio

xserver related

