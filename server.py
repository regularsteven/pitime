#!/usr/bin/python3
import io

import logging
import socketserver
from datetime import datetime
from threading import Condition
from http import server
import threading, os, signal
from os import system
import subprocess
from subprocess import check_call, call
import sys
from urllib.parse import urlparse, parse_qs
import argparse



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
    siteRoot = "/home/steven/Documents/dev/pitime"
else: 
    siteRoot = "/home/pi/pitime"
    

os.chdir(siteRoot+"/")


#start up the streamer, this will run as a child on a different port
#system("python3 streamer.py")

ipath = siteRoot+"/streamer.py"    #CHANGE PATH TO LOCATION OF mouse.py

def thread_second():
    call(["python3", ipath])

def check_kill_process(pstring):
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        os.kill(int(pid), signal.SIGKILL)


def startTimelapse() :
    print("start startTimelapse")
    system('./go.sh')

    print("end startTimelapse")
    return "cool"

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
        settings = " --ss "+ss+" --iso "+iso+" --awbg "+awbg
        filename = "img_"+current_time+"_ss-"+str(ss)+"_iso-"+str(iso)+"_awbg-"+awbg+"_manual.jpg"


    print("start shootPreview")
    sysCommand = "python3 preview.py --filename "+filename + settings
    print(sysCommand)
    system(sysCommand)
    print("end shootPreview")
    processThread = threading.Thread(target=thread_second)
    processThread.start()
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
    
    #processThread = threading.Thread(target=thread_second)
    #processThread.start()
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
                check_kill_process("streamer.py")
                startTimelapse()
            if actionVal == "preview" :
                check_kill_process("streamer.py")
                jsonResp += ',"filename":"'+shootPreview(query_components)+'"'
               
            
            
            jsonResp += '}'
            print(actionVal)
             # Whenever using 'send_header', you also have to call 'end_headers'
            self.end_headers()
            # Writing the HTML contents with UTF-8
            self.wfile.write(bytes(jsonResp, "utf8"))
            return
        elif self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        
        else :
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

        #self.send_error(404)
        #self.end_headers()



# Create an object of the above class
handler_object = MyHttpRequestHandler

my_server = socketserver.TCPServer(("", PORT), handler_object)
print("my_server running on PORT" + str(PORT))
# Star the server
my_server.serve_forever()
