import os
import socketserver
from http import server
from urllib.parse import urlparse, parse_qs
import subprocess
from subprocess import check_call, call
import threading, signal
import letslapse.utils as utils
from time import sleep

PORT = 80

siteRoot = "/home/steven/letslapse"



def start_server():
    # Create an object of the above class
    handler_object = MyHttpRequestHandler

    my_server = socketserver.TCPServer(("", PORT), handler_object)
    print("my_server running on PORT" + str(PORT))
    # Star the server
    my_server.serve_forever()


# Define other routes and handlers here

if __name__ == '__main__':
    start_server()  # For testing purposes
