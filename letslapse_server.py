#!/usr/bin/python3
import os
instanceCount = 0
for line in os.popen("ps -f -C python3 | grep letslapse_server.py"):
    instanceCount = instanceCount + 1
    if instanceCount > 1:
        print("letslapse_server.py: Instance already running - exiting now")
        exit()

from time import sleep
import subprocess
import io
import logging
import socketserver
from datetime import datetime
from threading import Condition
from http import server
import threading, signal
from os import system, path
import json
from subprocess import check_call, call
import sys
from urllib.parse import urlparse, parse_qs
import argparse

#my own custom utilities extracted for simpler structure 
import browser


PORT = 80

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('--testing', type=str,
                    help='Local development testing')
                    
args = parser.parse_args()
localDev = False
if args.testing == "True":
    localDev = True


if localDev:
    print("Running in testing mode for localhost development")
    siteRoot = os.getcwd()
else: 
    siteRoot = "/home/pi/letslapse"
    

os.chdir(siteRoot+"/")


#start up the streamer, this will run as a child on a different port
#system("python3 letslapse_streamer.py")

letslapse_streamerPath = siteRoot+"/letslapse_streamer.py"    #CHANGE PATH TO LOCATION OF letslapse_streamer.py

def letslapse_streamer_thread():
    call(["python3", letslapse_streamerPath])

def check_kill_process(pstring):
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        os.kill(int(pid), signal.SIGKILL)


def startTimelapse(shootName) :
    system('nohup python3 timelapse-auto.py --folderName '+shootName+' &')
    return "startTimelapse function complete"

def shootPreview(query_components) :
    mode = query_components["mode"][0]
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    settings = ""
    if mode == "auto": 
        filename = "img_"+current_time+"_auto.jpg"
        settings = " --mode auto"
    else : 
        ss = query_components["ss"][0]
        iso = query_components["iso"][0]
        awbg = query_components["awbg"][0]
        raw = query_components["raw"][0]
        settings = " --ss "+ss+" --iso "+iso+" --awbg "+awbg + " --raw "+raw
        filename = "img_"+current_time+"_ss-"+str(ss)+"_iso-"+str(iso)+"_awbg-"+awbg+"_manual.jpg"


    print("start shootPreview")
    sysCommand = "python3 preview.py --filename "+filename + settings
    print(sysCommand)
    system(sysCommand)
    print("end shootPreview")
    #processThread = threading.Thread(target=letslapse_streamer_thread)
    #processThread.start()
    return filename


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class MyHttpRequestHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(urlparse(self.path))
        query_components = parse_qs(urlparse(self.path).query)
        if 'action' in query_components:
            # Sending an '200 OK' response
            self.send_response(200)
            # Setting the header
            self.send_header("Content-type", "application/json")
            actionVal = query_components["action"][0]

            # Some custom HTML code, possibly generated by another function
            jsonResp = '{'
            jsonResp += '"completedAction":"'+actionVal+'"'
            
            if actionVal == "timelapse" :
                check_kill_process("letslapse_streamer.py")
                #check to see if this timelapse project is already in place - don't make a new one, if so
                shootName = query_components["shootName"][0]
                
                jsonResp += ',"shootName":"'+shootName+'"'
                if path.isfile("progress.txt") == True:
                    jsonResp += ',"error":false'
                    
                    jsonResp += ',"message":"resuming"'
                    #must be continuing the shoot
                    startTimelapse(shootName)

                elif path.isdir("auto_"+shootName) == True :
                    print("project with the same name already in use")
                    jsonResp += ',"error":true'
                    jsonResp += ',"message":"used"'
                else: 
                    #this instance is a new shoot
                    jsonResp += ',"error":false'
                    jsonResp += ',"message":"starting"'
                    startTimelapse(shootName)
                sleep(3) #gives time for the timelapse to start
                
            elif actionVal == "preview" :
                jsonResp += ',"filename":"'+shootPreview(query_components)+'"'
            elif actionVal == "killtimelapse" :
                check_kill_process("timelapse-auto.py")
                if query_components["pauseOrKill"][0] == "kill":
                    system("rm progress.txt")
            elif actionVal == "killstreamer" :
                check_kill_process("letslapse_streamer.py")
            elif actionVal == "startstreamer" :
                processThread = threading.Thread(target=letslapse_streamer_thread)
                processThread.start()
                #shellResp = subprocess.check_output("python3 letslapse_streamer.py", shell=True)
                #sleep(4) #ideally this would wait for a callback, but this allows the camera to start
            elif actionVal == "uptime" :
                uptime = subprocess.check_output("echo $(awk '{print $1}' /proc/uptime) | bc", shell=True)
                hostname = os.uname()[1]
                print(float(uptime))
                jsonResp += ',"seconds":"'+str(float(uptime))+'"'
                jsonResp += ',"hostname":"'+str(hostname)+'"'
            elif actionVal == "updatecode" :
                myhost = os.uname()[1]
                jsonResp += ',"hostname":"'+myhost+'"'
                updatecode = "git --git-dir=/home/pi/letslapse/.git pull"
                if(myhost == "gs66"):
                    updatecode = "git --git-dir="+siteRoot+"/.git pull"
                updateCodeResp = subprocess.check_output(updatecode, shell=True).strip()
                #updateCodeResp.split()
                jsonResp += ',"updateCodeResp":'+str(json.dumps(updateCodeResp.decode('utf-8')))
                #print(updatecode)
            elif actionVal == "listshoots":
                #for display of projects and still shots
                print("tbc")
                folderLen = (len(next(os.walk('.'))[1]))
            
            elif actionVal == "getStills":
                
                jsonResp += ',"stills":'+str( json.dumps( browser.getStills() ) )
                #print(browser.getShoots("0.jpg"))
            
            elif actionVal == "getShoots":
                
                jsonResp += ',"gallery":'+str( json.dumps( browser.getShoots("0.jpg") ) )
                #print(browser.getShoots("0.jpg"))

            elif actionVal == "systemstatus" :
                #pull all system status for simple startup script
                #diskspace / free space on device ######## df
                #device name ######## os.uname()[1]
                #timelapse in progress ######## ps -f -C python3 | grep timelapse-auto.py
                
                print(actionVal)
                #check_kill_process("letslapse_streamer.py")
                #startTimelapse(query_components["shootName"][0])
            elif actionVal == "quit" :
                exit()

            jsonResp += '}'
            print(actionVal)
             # Whenever using 'send_header', you also have to call 'end_headers'
            self.end_headers()
            # Writing the HTML contents with UTF-8
            self.wfile.write(bytes(jsonResp, "utf8"))

            if actionVal == "exit" :
                check_kill_process("timelapse-auto.py")
                check_kill_process("letslapse_streamer.py")
                exit()
            if actionVal == "shutdown" :
                check_kill_process("timelapse-auto.py")
                check_kill_process("letslapse_streamer.py")
                system("sudo shutdown now")
            elif actionVal == "reset" :
                check_kill_process("timelapse-auto.py")
                check_kill_process("letslapse_streamer.py")
                system("sudo reboot now")
            
            return
        elif self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        
        else :

            #if an image is requested that doesn't exist, it's probably a thumbnail request - in this event, extract it from the image and save it
            if self.path.endswith('_thumb.jpg'):
                if path.isfile(siteRoot+self.path) == False:
                    print("Extract the thum - it's not available. Temp function, should kill this")
                    exifCommand = "exiftool -b -ThumbnailImage "+siteRoot+self.path.replace("_thumb", "")+" > "+siteRoot+self.path
                    
                    exifProcess = subprocess.check_output(exifCommand, shell=True)
                
            if self.path == "/progress.txt":
                print("LOOKING FOR PATH")
                if path.isfile(siteRoot+self.path) == False:
                    print("PROGRESS.txt NOT FOUND CASE")
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes("", "utf8"))
                else :
                    self.send_response(200)
                    self.end_headers()
                    with open(siteRoot+self.path, 'rb') as file: 
                        self.wfile.write(file.read())

            else:
                print("General FILE serving")
                self.send_response(200)
                
                if self.path.endswith('.svg'):
                    self.send_header('Content-Type', 'image/svg+xml')
                if self.path.endswith('.css'):
                    self.send_header('Content-Type', 'text/css')
                if self.path.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript')
                if self.path.endswith('.jpg'):
                    self.send_header('Content-Type', 'image/jpeg')
                else:
                    self.send_header('Content-Type', 'text/html')

                
                self.end_headers()
                
                with open(siteRoot+self.path, 'rb') as file: 
                    self.wfile.write(file.read())
            
                
            #self.send_response(200)
            #self.send_header('Content-Type', 'text/html')
            #return http.server.SimpleHTTPRequestHandler.do_GET(self)

        #



#on strartup, if progress.txt is in place, then a boot has happened and the shoot should restart
if path.isfile("progress.txt") == True:
    file1 = open('progress.txt', 'r')
    Lines = file1.readlines()
    shootName = (Lines[1].strip())
    print("System restarted - progress.txt indicated shoot in progress")
    startTimelapse(shootName)


# Create an object of the above class
handler_object = MyHttpRequestHandler

my_server = socketserver.TCPServer(("", PORT), handler_object)
print("my_server running on PORT" + str(PORT))
# Star the server
my_server.serve_forever()


