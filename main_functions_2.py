__author__ = 'Robin'

import util
import shutil
import os
import urllib2
import json
from subprocess import Popen
import psutil
import itertools
import time
import subprocess
# Performance:
#-flop local, results local, no jsons: 115sec per 5000 keys.
#-flop local, results external, no jsons: 300sec per 5000keys.
#-flop external, results external, no jsons:

# Locations
PIO_DIR = 'C:\\Users\\robinvankappel\\Downloads\\Pio\\'
PIO_NAME = "PioSOLVER-edge19.exe"
PIO_LOC = PIO_DIR + PIO_NAME
FLOP_FOLDER = 'INPUT_flops' #for input folder in main folder
RESULTS_FOLDER = 'OUTPUT_results'
MAIN_FOLDER = 'generated_scripts'
FLOP_DIR = 'Z:\\test2\\' #for input folder full path
RESULTS_DIR = 'Z:\\pio_results\\' #or set to local folder 'OUTPUT_results'
JSON_DIR = 'Z:\\jsons_ready_for_db\\' #folder where jsons are saved
PROCESSED_FLOPS_DIR = 'Z:\\processed_trees\\'
# Settings for solving:
STEP_SIZE = 500 #number of keys retrieved in one Pio command
FLOP_LOCAL_INPUT_FOLDER = False #if true local disk is used for flop inputs
FLOP_LOCAL_RESULTS_FOLDER = True #if true local disk is used for pio output results files
MOVE_RESULTS = True #copy results from local folder to external folder
MAKE_JSON = False
REMOVE_PIO_OUTPUTS = False
LOG_SOLVED_FLOPS = True
MOVE_PROCESSED_FLOPS = True
# Tree properties (used in Pio solver):
pot_type = 's' #3bet = 3, 4bet = 4, single raised pot = s
bet_size = 2.5 #x big blind (e.g. 2.5 or 4)

#subprocess.call([PIO_DIR+PIO_NAME, TARGET])
"""
### CONTEXT:
# DB contains key-value pairs:
# key = [pot type, opening bet,flop,situation]
# value = [betsize1,betsize2(etc),check,call,fold]
### GOALS:
# Retrieve results for key
### STEPS:
# Loop over definition of (subset) of flops (e.g. from txt file)
# Run Pio script: built tree script (bat)   TODO
# Run Pio script: get lines from tree (bat) TODO
# Get all keys from lines
# Built Pio script to retrieve tree results
# Run Pio script: retrieve results
# Build json from results and send to API


### APPROACH for generating all keys:
## 1. brute force approach --> time requirements?
## 2. define all keys per flop --> if tree changes, then this would require a full manual redefine of this.
## 3. read keys from tree --> 10M keys per flop could require a lot of time
"""

def get_results2(path_app):
    #get all folder locations
    flop_dir, temp_flop_dir, output_dir, lines_dir, helpers_dir, json_dir = get_dirs(path_app)
    #get all flop files
    flops = util.get_flops(flop_dir)
    #get all cards existing in poker
    cards = util.get_pokercards()
    print 'Starting with processing flops...'
    start = time.time()
    for flop in flops[0:3]:#todo: iterate and save over multiple flops
        print util.getTime(start, flop) + 'flop: ' + str(flop.name)

        ###Function to copy flop to local disk because of performance
        if FLOP_LOCAL_INPUT_FOLDER == False:
            print 'Copy flop to local disk...'
            shutil.copy2(flop.path,temp_flop_dir) #copy flop to local disk
            new_flop_path = temp_flop_dir + flop.name + 'cfr'  # set new flop as flop
            util.wait_till_copy_finished(new_flop_path)
            print util.getTime(start) + 'finished copying'
            flop.path = new_flop_path #set new flop as flop
            ###

        ## -- OPTION 1: GENERATE KEYS FROM FILE WITH ALL LINES WITHOUT TURN AND RIVER CARDS--
        #uncomment line below to generate script to retrieve lines, then run script in Pio.
        line_file, line_script = build_script_to_get_lines(flop, lines_dir, helpers_dir)
        #build batch which runs the line_file
        batch_lines = build_batch_to_get_floplines(line_script,helpers_dir)
        #run batch file to run the script in Pio which retrieves the lines
        print 'Writing files for retrieving lines...'
        if (util.BatchWriteIsDone(998, batch_lines)):
            p = Popen(batch_lines, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print  util.getTime(start) + 'retrieving lines with Pio...'
        else:
            print 'failed opening batch file to get lines'
            exit(1)
        # get the keys from the file created by Pio
        print util.getTime(start) + 'getting keys from lines...'
        if (util.FileWriteIsDone(998, line_file)):
             keys = util.get_keys_from_file(line_file,flop,cards)
             for proc in psutil.process_iter():
                if proc.name() == PIO_NAME:
                    proc.terminate()
             print util.getTime(start) + 'retrieved all keys'
        else:
            print 'failed reading lines from file'
            exit(1)

        print 'largest key has ' + str(len(max(keys,key=len))+12-2) + ' characters'
        keys = keys[0:500]#test
        #make subset of keys such that entire process is split in parts, for computational reasons.
        step_size = STEP_SIZE
        keys_iter = list()
        for key_iter in itertools.islice(range(len(keys)-1), 0, len(keys), step_size):
            keys_iter.append(key_iter)
        keys_iter.append(len(keys)-1)

        print 'Total amount of keys to process: ' + str(len(keys))
        for i,value in enumerate(keys_iter):
            if not i == 0:
                start_time_subkeys = time.time()
                print 'Processing keys ' + str(keys_iter[i-1]) + ' till ' + str(keys_iter[i]) + '...'
                subkeys = keys[keys_iter[i-1]:keys_iter[i]]
                #build one scripts per flop which can generate the results for all keys incl. actions (=children)
                pio_results_outputs,pio_results_file = build_script_to_generate_results_all_keys(subkeys, flop, helpers_dir, output_dir)
                batch_results = build_batch_results_all_keys(pio_results_file,helpers_dir)

                #run batch file to run the script in Pio which generates the results of all keys
                print 'Generating batch file to retrieve tree results...'
                if (util.BatchWriteIsDone(998, batch_results)):
                     q=Popen(batch_results,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                     print  util.getTime(start) + 'retrieving results with Pio...'
                else:
                    print 'failed opening batch file to get results'
                    exit(1)

                if MAKE_JSON == True:
                    print util.getTime(start) + 'making jsons of all key from results...'
                    for j,key in enumerate(subkeys):
                        pio_results_output = pio_results_outputs[j]
                        full_key = flop.name + '_' + str(pot_type) + '_' + str(int(bet_size*10.0)) + '_' + key.replace(':','_')
                        json_dir_flop =  json_dir + flop.name + '\\'
                        if not os.path.exists(json_dir_flop):
                            os.makedirs(json_dir_flop)
                        json_file = json_dir_flop + full_key + '.bz2'
                        # create json and write to file
                        try:
                            if (util.FileWriteIsDone(998, pio_results_output)):
                                 json_object,payload = create_json(json_file,pio_results_output)
                            else:
                                print 'failed reading results from file'
                                exit(1)
                        except:
                            henk=1#todo: check what is happening...??

                        #optimise output_script
                        #response = send_json(full_key,payload) #todo: test and activate.
                        #remove json after sending to DB:
                        #if os.path.exists(json_file):
                            #os.remove(json_file)
                else:
                    util.FileWriteIsDone(998, pio_results_outputs[-1])

                print util.getTime(start) + 'finished processing ' + str(
                    keys_iter[i] - (keys_iter[i - 1])) + ' keys in ' + str(int(time.time() - start_time_subkeys)) + 's'

                for proc in psutil.process_iter():
                    if proc.name() == PIO_NAME:
                        proc.terminate()

                #move resulting files to different folder
                if MOVE_RESULTS:
                    files_to_move = pio_results_outputs[:]
                    dest_folder = RESULTS_DIR + flop.name + '\\'
                    if not os.path.exists(dest_folder):
                        os.mkdir(dest_folder)
                    for file in files_to_move:
                        shutil.move(file,dest_folder)

                #remove pio outputs
                if REMOVE_PIO_OUTPUTS:
                    print util.getTime(start) + 'remove Pio result files...'
                    for pio_results_output in pio_results_outputs:
                        if os.path.exists(pio_results_output):
                            os.remove(pio_results_output)

        print util.getTime (start) + 'finished processing flop'

        if LOG_SOLVED_FLOPS:
            #save in log file which flops are solved
            log_solved_flops(flop, output_dir, keys)

        if MOVE_PROCESSED_FLOPS:
            #move processed flop to different folder:
            print 'move processed flop'
            os.rename(flop.path, PROCESSED_FLOPS_DIR)

        # ## -- OPTION 2: GENERATE KEYS FROM MANUAL INPUT FILE WITH ONLY ALL-IN LINES --
        # # #get all key possibilities from input file (user defined); should match with tree settings of flops.
        # # lines = get_lines(lines_dir + 'used_lines_in_flops.txt', flop, cards)
        # # #retrieve all possible keys from lines (make class keys with keys.values and keys.actions)
        # # keys = util.get_keys(lines)
        # for key in keys[0:10]:
        #     #build all scripts per flop which can generate the results per key incl. actions (=children)
        #     pio_results_output,pio_results_file = build_script_to_generate_results_per_key(key, flop, helpers_dir, output_dir)
        #     #run batch file to run the script in Pio which retrieves the lines,
        #     full_key = flop.name + '_' + str(pot_type) + '_' + str(int(bet_size*10.0)) + '_' + key.replace(':','_')
        #     json_file = json_dir + '\\' + full_key + '.txt'
        #     #todo: results file incl full key should be input for making batch file.
        #     batch_results = build_batch_results_per_key(pio_results_file,helpers_dir)
        #     Popen(batch_results)
        #     # create json and write to file
        #     if (util.FileWriteIsDone(998, pio_results_output)):
        #          json_object,payload = create_json(json_file,pio_results_output)
        #     else:
        #         print 'failed reading results from file'
        #         exit(1)
        #     #optimise output_script
        #
        #     response = send_json(full_key,payload)
    return 0

def log_solved_flops(flop, output_dir, keys):
    log_file = output_dir + 'solved-flops2.log'
    with open(log_file, 'a') as f:
        content = flop.name + ' (' + str(len(keys)) + ' keys)' + '\n'
        print content
        print '\n'
        f.write(content)
    return log_file

def build_batch_results_per_key(pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results.bat'
    with open(batch_file, 'w+') as f:
        content = 'set root=C:\Users\Robin\Documents\Pio' + '\n'
        content += 'cd %root%' + '\n'
        content += 'start C:\Users\Robin\Documents\Pio\PioSOLVER-edge19.exe ' + pio_results_file + '\n'
        print 'Script for getting results of Pio'
        print content
        print '\n'
        f.write(content)
    return batch_file

def build_batch_results_all_keys(pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results.bat'
    if os.path.isfile(batch_file):
        os.remove(batch_file)
    with open(batch_file, 'w+') as f:
        content = 'set root=' + PIO_DIR + '\n'
        content += 'cd %root%' + '\n'
        content += 'start ' + PIO_LOC + ' ' + pio_results_file + '\n'
        # print 'Script for getting results of Pio'
        # print content
        # print '\n'
        f.write(content)
    return batch_file

def build_batch_to_get_floplines(pio_lines_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_lines.bat'
    if os.path.isfile(batch_file):
        os.remove(batch_file)
    with open(batch_file, 'w+') as f:
        content = 'set root=' + PIO_DIR + '\n'
        content += 'cd %root%' + '\n'
        content += 'start ' + PIO_LOC + ' ' + pio_lines_file + '\n'
        # print 'Script for getting results of Pio'
        # print content
        # print '\n'
        f.write(content)
    return batch_file

def send_json(key,payload):
    url = 'http://5.79.87.151/app_dev.php/' + key
    req = urllib2.Request(url)
    req.add_header('content-type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(payload))
    return response

def get_lines(file,flop,cards):
    lines = list()
    with open(file, 'r') as f:
        for v_line in f:
            # get the line without varying turn or river card
            default_line = util.get_default_line(v_line)
            lines_per_default_line = util.generate_lines(default_line,flop,cards)
            lines.extend(lines_per_default_line)
        #print lines
    return lines

def build_script_to_get_lines(flop, lines_dir, helpers_dir):
    # make script per flop
    helper_script = helpers_dir + flop.name + '_getlines.txt'
    if os.path.isfile(helper_script):
        os.remove(helper_script)
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    output_file = lines_dir + 'used_lines_in_flop-' + flop.name + '.txt'
    #remove file if it already exists
    if os.path.isfile(output_file):
        os.remove(output_file)
    with open(helper_script, 'w+') as f:
        content = 'load_tree ' + '"' + flop.path + '"' + '\n'
        content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
        content += 'show_all_freqs local ' + '\n'
        #print 'Script for retrieving lines of tree:'
        #print content
        #print '\n'
        f.write(content)
    return output_file, helper_script

def build_script_to_generate_results_per_key(key, flop, helpers_dir, output_dir):
    # make script per flop
    helper_script = helpers_dir + flop.name + '_' + key.replace(':','_') + '.txt'
    if os.path.isfile(helper_script):
        os.remove(helper_script)
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    output_file = output_dir + flop.name + '-' + key.replace(':','_') + '.txt'
    if os.path.isfile(output_file):
        os.remove(output_file)
    with open(helper_script, 'w+') as f:
        content = 'load_tree ' + '"' + flop.path + '"' + '\n'
        content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
        content += 'show_strategy_pp ' + key + '\n'
        #content += 'show_children ' + key + '\n'
        print content
        f.write(content)
    return output_file, helper_script

def build_script_to_generate_results_all_keys(keys, flop, helpers_dir, output_dir):
    # make script per flop
    helper_script = helpers_dir + flop.name + '.txt'
    if os.path.isfile(helper_script):
        os.remove(helper_script)
    output_flop_dir = output_dir + flop.name + '\\'
    if not os.path.exists(output_flop_dir):
        os.makedirs(output_flop_dir)
    output_files = list()
    with open(helper_script, 'w+') as f:
        content = 'load_tree ' + '"' + flop.path + '"' + '\n'
        for key in keys:
            output_file = output_flop_dir + flop.name + '-' + key.replace(':','_') + '.txt'
            output_files.append(output_file)
            if os.path.isfile(output_file):
                os.remove(output_file)
            content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
            content += 'show_strategy_pp ' + key + '\n'
            content += 'show_children ' + key + '\n'
        #print content
        f.write(content)
    return output_files, helper_script

def create_json(json_file,pio_results_file):
    #temp for testing
    with open(pio_results_file,'r+') as f:
        file = f.read()
        split_file = file.split('\n')
        #find lines with children and extract action
        actions,i = util.get_actions_and_end_of_file(split_file)
        json,response = util.build_json(split_file,actions,i,json_file)
    f.closed
    return json,response

def get_dirs(path_app):
    work_dir = os.path.join(path_app,MAIN_FOLDER)+'\\'
    if FLOP_LOCAL_INPUT_FOLDER:
        flop_dir = os.path.join(work_dir,FLOP_FOLDER)+'\\'
    else:
        flop_dir = FLOP_DIR
    temp_flop_dir = os.path.join(work_dir,FLOP_FOLDER)+'\\'
    if FLOP_LOCAL_RESULTS_FOLDER:
        output_dir = os.path.join(work_dir,RESULTS_FOLDER)+'\\'
    else:
        output_dir = RESULTS_DIR
    lines_dir = os.path.join(work_dir,'lines')+'\\'
    helpers_dir = os.path.join(work_dir,'helper_scripts')+'\\'
    #json_dir = os.path.join(work_dir,'json_files')+'\\'
    json_dir = JSON_DIR
    if not os.path.exists(work_dir):
            os.makedirs(work_dir)
    if not os.path.exists(flop_dir):
            os.makedirs(flop_dir)
    if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    if not os.path.exists(lines_dir):
            os.makedirs(lines_dir)
    if not os.path.exists(helpers_dir):
            os.makedirs(helpers_dir)
    if not os.path.exists(json_dir):
            os.makedirs(json_dir)
    return flop_dir, temp_flop_dir, output_dir, lines_dir, helpers_dir, json_dir



