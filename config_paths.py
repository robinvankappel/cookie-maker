##### LOG PARAMETERS #####
LOG_NAME = 'solved-flops.log'
#____________________________

####### SETTINGS GOOGLE INSTANCE ########
#PIO SETTINGS
PIO_DIR = 'C:\\Users\\j_moene\\Desktop\\pio\\'
PIO_NAME = "PioSOLVER-edge19AVX.exe"
PIO_LOC = PIO_DIR + PIO_NAME

#PATH SETTINGS (GLOBAL VARS)
MAIN_FOLDER = 'generated_scripts'
FLOP_FOLDER = 'INPUT_flops_srp\\flops_to_process-test_set'  # used when FLOP_LOCAL_INPUT_FOLDER = True
RESULTS_FOLDER = 'OUTPUT_results'  # used when FLOP_LOCAL_RESULTS_FOLDER = True
#FLOP_DIR = 'D:\\3betFinal4x\\'  # used when FLOP_LOCAL_INPUT_FOLDER = False
FLOP_DIR = 'E:\\db-filler\\generated_scripts\\'
RESULTS_DIR = 'D:\\solved_trees_3B\\pio_results\\'  # used when FLOP_LOCAL_RESULTS_FOLDER = False
#PROCESSED_FLOPS_DIR = 'C:\\Users\\J. Moene\\Desktop\\CookieMonster_pythonfiles\\db-filler\\generated_scripts\\INPUT_flops_3B\\processed_flops\\'
PROCESSED_FLOPS_DIR = 'E:\\db-filler\\generated_scripts\\INPUT_flops_srp\\processed_flops-test_set'
FLOP_LOCAL_INPUT_FOLDER = True  # if true local disk is used for flop inputs
FLOP_LOCAL_RESULTS_FOLDER = True  # if true local disk is used for pio output results files
MOVE_RESULTS = False  # copy results from local folder to external folder
MOVE_PROCESSED_FLOPS = True  # move the flops which have been handled to PROCESSED_FLOPS_DIR
LINES_FILE = 'USED_LINES_IN_FLOP_srp-25x.txt'
USE_POWERSHELL = True #for Google_instance (not required at PC Jelle)

#TREE PROPERTIES (used in Pio solver):
POT_TYPE = 's'  # 3bet = 3, 4bet = 4, single raised pot = s
BET_SIZE = 2.5  # x big blind (e.g. 2.5 or 4)
POTSIZEMAX = 2000
#POTSIZESTART = 200 #if POT_TYPE = 3
POTSIZESTART = 50 #if POT_TYPE = s

##### SETTINGS FOR SOLVING #####
STEP_SIZE = 1000  # number of keys retrieved in one Pio command
KEY_MIN_INDEX = 0#for testing purpose; default 0
KEY_MAX_INDEX = None#for testing purpose; default None
GENERATE_NEW_KEYS = True

##### SETTINGS JELLE PC #######
# #PIO SETTINGS
# PIO_DIR = 'C:\\Users\\"J. Moene"\\Desktop\\"pio edge"\\'
# PIO_NAME = "PioSOLVER-edge19AVX.exe"
# PIO_LOC = PIO_DIR + PIO_NAME
#
# #PATH SETTINGS (GLOBAL VARS)
# MAIN_FOLDER = 'generated_scripts'
# FLOP_FOLDER = 'INPUT_flops_3B\\flops_being_processed'  # used when FLOP_LOCAL_INPUT_FOLDER = True
# RESULTS_FOLDER = 'OUTPUT_results'  # used when FLOP_LOCAL_RESULTS_FOLDER = True
# #FLOP_DIR = 'D:\\3betFinal4x\\'  # used when FLOP_LOCAL_INPUT_FOLDER = False
# FLOP_DIR = 'F:\\flops_to_process\\3B_4x\\'
# RESULTS_DIR = 'D:\\solved_trees_3B\\pio_results\\'  # used when FLOP_LOCAL_RESULTS_FOLDER = False
# #PROCESSED_FLOPS_DIR = 'C:\\Users\\J. Moene\\Desktop\\CookieMonster_pythonfiles\\db-filler\\generated_scripts\\INPUT_flops_3B\\processed_flops\\'
# PROCESSED_FLOPS_DIR = 'F:\\flops_processed\\3B_4x\\'
# FLOP_LOCAL_INPUT_FOLDER = False  # if true local disk is used for flop inputs
# FLOP_LOCAL_RESULTS_FOLDER = True  # if true local disk is used for pio output results files
# MOVE_RESULTS = False  # copy results from local folder to external folder
# MOVE_PROCESSED_FLOPS = True  # move the flops which have been handled to PROCESSED_FLOPS_DIR
# LINES_FILE = 'USED_LINES_IN_FLOP_3B-4x.txt'
#
# #TREE PROPERTIES (used in Pio solver):
# POT_TYPE = '3'  # 3bet = 3, 4bet = 4, single raised pot = s
# BET_SIZE = 4  # x big blind (e.g. 2.5 or 4)
# POTSIZEMAX = 2000
# POTSIZESTART = 200 #if POT_TYPE = 3
# #POTSIZESTART = 50 #if POT_TYPE = s
#
# ##### SETTINGS FOR SOLVING #####
# STEP_SIZE = 1000  # number of keys retrieved in one Pio command
# KEY_MIN_INDEX = 0#for testing purpose; default 0
# KEY_MAX_INDEX = None#for testing purpose; default None
# GENERATE_NEW_KEYS = True