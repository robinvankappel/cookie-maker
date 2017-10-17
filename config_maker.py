import sys
sys.path.append('D:\cookie')
from config_cookie import *

##### LOG PARAMETERS #####
LOG_NAME = 'solved-flops.log'
#____________________________

##### SETTINGS FOR SOLVING #####
KEY_MIN_INDEX = 0#for testing purpose; default 0
KEY_MAX_INDEX = 3000#for testing purpose; default None
USE_POWERSHELL = True

####### PATH SETTINGS LEASEWEB INSTANCE ########
PIO_LOC = PIO_DIR + PIO_NAME


#TREE PROPERTIES (used in Pio solver):
class Settings():
    """
    Make object with all
    """
    def __init__(self,flop):
        if flop.stacksize == 60:
            if flop.type == 's':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 2.2
            elif flop.type == '3':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 6.6
            elif flop.type == '4':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 14.9
        elif flop.stacksize == 100:
            if flop.type == 's':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 2.5
            elif flop.type == '3':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 10
            elif flop.type == '4':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 25
        elif flop.stacksize == 140:
            if flop.type == 's':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 2.5
            elif flop.type == '3':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 10
            elif flop.type == '4':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 30
            elif flop.type == '5':
                self.STEP_SIZE = 1000
                self.BET_SIZE = 50
        self.LINEFILE = 'USED_LINES_IN_FLOP_' + str(flop.stacksize) + '-' + flop.type + '-' + str(self.BET_SIZE) + 'BB.txt'
        self.POTSIZEMAX = flop.stacksize * 2 * 10
        self.POTSIZESTART = self.BET_SIZE * 2 * 10




##### SETTINGS JELLE PC #######
#PIO SETTINGS
# PIO_DIR = 'C:\\Users\\"J. Moene"\\Desktop\\bs\\"New folder"\\"pio edge"\\'
# PIO_NAME = "PioSOLVER-edge19AVX.exe"
# PIO_LOC = PIO_DIR + PIO_NAME