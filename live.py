
from os import system
from time import sleep

#from pydng.core import RPICAM2DNG
from datetime import datetime




import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('ip_arg', type=str,
                    help='A required integer positional argument')


args = parser.parse_args()

now = datetime.now()

current_time = now.strftime("%H_%M_%S")
print("tcp://"+args.ip_arg+":3333")

 
#sleep(2)
#d=RPICAM2DNG()

# -r = append raw file for later processing




system("raspivid -t 0 -l -o tcp://"+args.ip_arg+":3333 -w 1280 -h 720")
