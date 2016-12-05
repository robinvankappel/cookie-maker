__author__ = 'Robin'

import util
import shutil
import os
import urllib2
import json
import itertools
import time
import subprocess
import bz2
from itertools import islice

KEY_MIN_INDEX = 0#for testing purpose; default 0
KEY_MAX_INDEX = 9999999999#for testing purpose; default None
WRITE_JSON = False
BATCHING_PIO_RESULTS = True

# Performance results:
#-flop local, results local, no jsons: 115sec per 5000 keys.
#-flop local, results external, no jsons: 300sec per 5000keys.
#-flop external, move2local, results local, move2external, no jsons: 6200s for 30k keys
#todo: if tree name is wrong, script fails.


#Global variables
PIO_DIR = 'C:\\Users\\robinvankappel\\Desktop\\pio\\'
PIO_NAME = "PioSOLVER-edge19.exe"
PIO_LOC = PIO_DIR + PIO_NAME
URL_DB_SERVER = 'http://104.155.43.38/app_dev.php/'
"""
### CONTEXT:
# DB contains key-value pairs:
# key = [pot type, opening bet,flop,situation]
# value = [betsize1,betsize2(etc),check,call,fold]
### GOALS:
# Retrieve results for key
### STEPS:
# Loop over definition of (subset) of flops (e.g. from txt file)
# Run Pio script: built tree script (bat)
# Run Pio script: get lines from tree (bat)
# Get all keys from lines
# Built Pio script to retrieve tree results
# Run Pio script: retrieve results
# Build json from results and send to API


### APPROACH for generating all keys:
## 1. brute force approach --> time requirements?
## 2. define all keys per flop --> if tree changes, then this would require a full manual redefine of this.
## 3. read keys from tree --> 10M keys per flop could require a lot of time
"""

def get_results(path_app):
    #get all folder locations
    flop_dir, temp_flop_dir, output_dir, lines_dir, helpers_dir, json_dir = get_dirs(path_app)
    #get all flop files
    flops = util.get_flops(flop_dir)
    #get all cards existing in poker
    cards = util.get_pokercards()
    print 'Starting with processing flops in input folder...'
    start = time.time()
    for flop in flops:
        print util.getTime(start,flop) + 'flop: ' + str(flop.name)

        # save original flop location
        flop_path_original = flop.path

        #Function to copy flop to local disk because of performance
        if FLOP_LOCAL_INPUT_FOLDER == False:
            print util.getTime(start,flop)+'Copy flop to local disk...'
            copy_flop(flop,temp_flop_dir,start)

        ## -- OPTION 1: GENERATE KEYS FROM FILE WITH ALL LINES WITHOUT TURN AND RIVER CARDS--
        keys = get_all_keys(flop,lines_dir,helpers_dir,start,cards)#todo: test if lines are the same for different flops.

        print util.getTime(start, flop) + 'Total number of keys to process: ' + str(len(keys))

        if KEY_MAX_INDEX < len(keys):
            keys = keys[KEY_MIN_INDEX:KEY_MAX_INDEX]#for testing purpose
        else:
            keys = keys[KEY_MIN_INDEX:]
        #make subset of keys such that entire process is split in parts, for computational reasons.
        step_size = STEP_SIZE
        keys_iter = make_subset_keys(step_size, keys)

        #iterate over subsets
        for i,subset_end_index in enumerate(keys_iter):
            if not i == 0:
                start_time_subkeys = time.time()
                print util.getTime(start,flop) + 'Processing keys ' + str(keys_iter[i-1]) + ' till ' + str(keys_iter[i]) + '...'
                subkeys = keys[keys_iter[i-1]:keys_iter[i]]

                #get Pio results by building script and running it
                if BATCHING_PIO_RESULTS == False:
                    pio_results_outputs,new_pio_process = get_pio_results(subkeys, subset_end_index,flop, helpers_dir, output_dir, start)
                    if (util.FileWriteIsDone(pio_results_outputs[-1])):
                        new_pio_process.terminate()
                        time.sleep(2)  # wait for parallel processes to find PID.
                        if MAKE_JSON == True:
                            print util.getTime(start, flop) + 'making json content'
                            json_content = make_json(start, flop, subkeys, pio_results_outputs)
                            ## compress:
                            # compressed_json_content = bz2.compress(str(json_content))
                            print util.getTime(start, flop) + 'json content created'
                            if WRITE_JSON:
                                write_json_file(start, flop, json_dir, subset_end_index, json_content)
                            if SEND_JSON == True:
                                # send json to db
                                print util.getTime(start, flop) + 'sending json...'
                                send_json(json_content)
                                print util.getTime(start, flop) + 'json sent to db_server'
                                # if REMOVE_JSON_AFTER_SENDING_DB: # not necessary when explicit json files are not used
                                #     #remove json from disk after sent
                                #     if os.path.exists(json_file):
                                #         os.remove(json_file)#not tested, maybe deleted before sending to db
                elif BATCHING_PIO_RESULTS == True:
                    pio_results_output, new_pio_process = get_pio_results(subkeys, subset_end_index, flop, helpers_dir,
                                                                           output_dir, start)
                    if (util.FileWriteIsDone2(pio_results_output)):
                        new_pio_process.terminate()
                        time.sleep(2)  # wait for parallel processes to find PID.
                        #add subkeys to output file:
                        util.add_subkeys_and_metadata_to_output(subkeys,pio_results_output,POT_TYPE,BET_SIZE)
                        if MAKE_JSON == True:
                            print util.getTime(start, flop) + 'making json content'
                            json_content = make_json(start, flop, subkeys, pio_results_output)
                            ## compress:
                            # compressed_json_content = bz2.compress(str(json_content))
                            print util.getTime(start, flop) + 'json content created'
                            if WRITE_JSON:
                                write_json_file(start, flop, json_dir, subset_end_index, json_content)
                            if SEND_JSON == True:
                                # send json to db
                                print util.getTime(start, flop) + 'sending json...'
                                send_json(json_content)  # todo: test and activate.
                                print util.getTime(start, flop) + 'json sent to db_server'
                #test
                # if (util.FileWriteIsDone2(pio_results_outputs)):
                #     print util.getTime(start,flop) + 'black dick cock hammer smiling over your cumface'
                #     henk=1




                print util.getTime(start,flop) + 'finished processing ' + str(
                    keys_iter[i] - (keys_iter[i - 1])) + ' keys in ' + str(int(time.time() - start_time_subkeys)) + 's'

                # todo: move in parallel process.
                #move resulting files to different folder
                # if MOVE_RESULTS:
                #     print util.getTime(start, flop) + 'move results...'
                #     move_results(pio_results_outputs,flop)

                #remove pio outputs
                if REMOVE_PIO_OUTPUTS:
                    print util.getTime(start,flop) + 'remove Pio result files...'
                    if BATCHING_PIO_RESULTS == True:
                        if os.path.exists(pio_results_output):
                            os.remove(pio_results_output)
                    else:
                        for pio_results_output in pio_results_outputs:
                            if os.path.exists(pio_results_output):
                                os.remove(pio_results_output)

        print util.getTime(start,flop) + 'finished processing flop'

        if LOG_SOLVED_FLOPS:#todo: log per results file and/or json file
            print util.getTime(start, flop) + 'add flop to log'
            #save in log file which flops are solved
            log_file = log_solved_flops(flop, output_dir, keys)
            if MOVE_RESULTS:
                path, file = os.path.split(log_file)
                shutil.copyfile(log_file,RESULTS_DIR+file)

        if MOVE_PROCESSED_FLOPS:
            print util.getTime(start,flop) + 'move processed flop'
            #move processed flop to different folder:
            path,file = os.path.split(flop_path_original)
            os.rename(flop_path_original, PROCESSED_FLOPS_DIR+file)#rename original flop.path to path (not dir)

        if FLOP_LOCAL_INPUT_FOLDER == False:
            #delete (copied) flop on local disk
            print util.getTime(start, flop) + 'remove flop on local disk'
            os.remove(flop.path)
    return 0

# def move_results(pio_results_outputs,flop):
#     files_to_move = pio_results_outputs[:]
#     dest_folder = RESULTS_DIR + flop.name + '\\'
#     if not os.path.exists(dest_folder):
#         os.mkdir(dest_folder)
#     for file in files_to_move:
#         path,file_name = os.path.split(file)
#         dest_path = dest_folder + file_name
#         if os.path.exists(dest_path):
#             os.remove(dest_path)
        #shutil.move(file, dest_path)
        #subprocess.call(["xcopy", file, dest_path, "/K/O/X"])#test

        ##copy quick method.
        # import subprocess
        # import sys
        # file = r'C:\Users\robinvankappel\Downloads\CookieMonster\generated_scripts\OUTPUT_results\TsTd9c\TsTd9c_s_25_r_0.txt'
        # dest_path = r'Z:\pio_results\TsTd9c\TsTd9c_s_25_r_0.txt'
        # file_folder, file_name = os.path.split(file)
        # dest_folder, dest_file_name = os.path.split(dest_path)
        # devnull = open(os.devnull, 'w')
        # p = subprocess.check_call(["xcopy", "/y", file_folder, dest_folder], stdout=devnull)
        # sys.stdout = sys.__stdout__
    return

def make_json(start,flop,subkeys,pio_results_outputs):
    print util.getTime(start, flop) + 'making jsons of all keys from results...'
    if BATCHING_PIO_RESULTS == False:
        json_content = dict()
        for j, key in enumerate(subkeys):
            pio_results_output = pio_results_outputs[j]
            full_key = util.key2fullkey(flop,key,POT_TYPE,BET_SIZE)
            # create json and write to file
            json_content_of_key = create_json(pio_results_output)
            json_content[full_key] = json_content_of_key
    elif BATCHING_PIO_RESULTS == True:
        # create json and write to file
        json_content = create_json2(pio_results_outputs,flop,subkeys)
    return json_content

def write_json_file(start,flop,json_dir,keys_iter_value,json_content):
    print util.getTime(start, flop) + 'writing json_content of subset to file'
    json_flop_dir = json_dir + flop.name
    if not os.path.exists(json_flop_dir):
        os.makedirs(json_flop_dir)
    json_file = json_flop_dir + '\\' + flop.name + '_' + str(keys_iter_value) + '.txt'
    if os.path.exists(json_file):
        os.remove(json_file)
    # if util.DirWriteIsDone(json_flop_dir):
    with open(json_file, 'w+') as f:
        content = json.dumps(json_content)
        f.write(content)
    # else:
    #     print util.getTime(start, flop) + 'failed making directory to save json'
    return

def get_pio_results(subkeys, value,flop, helpers_dir, output_dir, start):
    # build one scripts per flop which can generate the results for all keys incl. actions (=children)
    if BATCHING_PIO_RESULTS == False:
        pio_results_outputs, pio_results_file = build_script_to_generate_results_all_keys(subkeys, flop, helpers_dir,output_dir)
    elif BATCHING_PIO_RESULTS == True:
        pio_results_output, pio_results_file = build_script_to_generate_results_all_keys_one_file(subkeys, value, flop, helpers_dir,output_dir)

    #build windows batch file to run Pio
    batch_results = build_batch_results_all_keys(flop,pio_results_file, helpers_dir)

    # run batch file to run the script in Pio which generates the results of all keys
    print util.getTime(start, flop) + 'Generating batch file to retrieve tree results...'
    if (util.BatchWriteIsDone(batch_results)):
        existing_pio_processes = util.get_all_processes(PIO_NAME)
        print util.getTime(start, flop) + 'running Pio to retrieve results...'
        q = subprocess.Popen(batch_results, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # wait till new Pio process is started:
        new_pio_process = util.get_new_process(existing_pio_processes, PIO_NAME)
        print util.getTime(start, flop) + 'corresponding Pio process found (PID:' + str(new_pio_process.pid) + ')'
    else:
        print util.getTime(start, flop) + 'failed opening batch file to get results'
        exit(1)

    if BATCHING_PIO_RESULTS == False:
        return pio_results_outputs, new_pio_process
    elif BATCHING_PIO_RESULTS == True:
        return pio_results_output, new_pio_process

def make_subset_keys(step_size, keys):
    keys_iter = list()
    for key_iter in itertools.islice(range(len(keys) - 1), 0, len(keys), step_size):
        keys_iter.append(key_iter)
    keys_iter.append(len(keys) - 1)
    return keys_iter

def get_all_keys(flop,lines_dir,helpers_dir,start,cards):
    # uncomment line below to generate script to retrieve lines, then run script in Pio.
    line_file, line_script = build_script_to_get_lines(flop, lines_dir, helpers_dir)
    # build batch which runs the line_file
    batch_lines = build_batch_to_get_floplines(flop,line_script, helpers_dir)
    # run batch file to run the script in Pio which retrieves the lines
    print util.getTime(start, flop) + 'Writing files for retrieving lines...'
    if (util.BatchWriteIsDone(batch_lines)):
        existing_pio_processes = util.get_all_processes(PIO_NAME)
        print util.getTime(start, flop) + 'Running Pio to retrieve lines...'
        p = subprocess.Popen(batch_lines, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #wait till new Pio process is started:
        new_pio_process = util.get_new_process(existing_pio_processes,PIO_NAME)
        print util.getTime(start,flop) + 'corresponding Pio process found (PID:' + str(new_pio_process.pid) + ')'
    else:
        print util.getTime(start, flop) + 'failed opening batch file to get lines'
        exit(1)

    # get the keys from the file created by Pio
    if (util.FileWriteIsDone(line_file)):
        if os.stat(line_file).st_size < 10000:
            print util.getTime(start,flop) + 'failed getting lines (line file < 10KB)'
        print util.getTime(start, flop) + 'getting keys from lines...'
        keys = util.get_keys_from_file(line_file, flop, cards)

        new_pio_process.terminate()
        time.sleep(2)#wait (longer than wait of sleep timer in get_new_process such that other process can continue)
        #util.kill_all_processes(PIO_NAME)
        print util.getTime(start, flop) + 'retrieved all keys'
    else:
        print util.getTime(start, flop) + 'failed reading lines from file'
        exit(1)
    return keys

def copy_flop(flop,temp_flop_dir,start):
    shutil.copy2(flop.path, temp_flop_dir)  # copy flop to local disk
    new_flop_path = temp_flop_dir + flop.name + '.cfr'  # set new flop as flop
    util.wait_till_copy_finished(new_flop_path)
    flop.path = new_flop_path  # set new flop as flop
    print util.getTime(start, flop) + 'finished copying'
    return new_flop_path

def log_solved_flops(flop, output_dir, keys):
    log_file = output_dir + LOG_NAME
    with open(log_file, 'a') as f:
        content = flop.name + ' (' + str(len(keys)) + ' keys)' + '\n'
        f.write(content)
    return log_file

def build_batch_results_per_key(pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results.bat'
    with open(batch_file, 'w+') as f:
        content = 'set root=C:\Users\Robin\Documents\Pio' + '\n'
        content += 'cd %root%' + '\n'
        content += 'start C:\Users\Robin\Documents\Pio\PioSOLVER-edge19.exe "' + pio_results_file + '"\n'
        print 'Script for getting results of Pio'
        print content
        print '\n'
        f.write(content)
    return batch_file

def build_batch_results_all_keys(flop,pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results' + flop.name + '.bat'
    if os.path.isfile(batch_file):
        os.remove(batch_file)
    with open(batch_file, 'w+') as f:
        content = 'set root=' + PIO_DIR + '\n'
        content += 'cd %root%' + '\n'
        content += 'start ' + PIO_LOC + ' "' + pio_results_file + '"\n'
        # print 'Script for getting results of Pio'
        # print content
        # print '\n'
        f.write(content)
    return batch_file

def build_batch_to_get_floplines(flop,pio_lines_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_lines-' + flop.name + '.bat'
    if os.path.isfile(batch_file):
        os.remove(batch_file)
    with open(batch_file, 'w+') as f:
        content = 'set root=' + PIO_DIR + '\n'
        content += 'cd %root%' + '\n'
        content += 'start ' + PIO_LOC + ' "' + pio_lines_file + '"\n'
        # print 'Script for getting results of Pio'
        # print content
        # print '\n'
        f.write(content)
    return batch_file

def send_json(json_content):
    url = URL_DB_SERVER + 'upload'
    req = urllib2.Request(url)
    req.add_header('content-type', 'application/json')
    #JSON_CHUNKS = 1000
    json_dump = json.dumps(json_content)
    try:
        #for k, v in islice(json_content.iteritems(), JSON_CHUNKS):
        response = urllib2.urlopen(req, json_dump)
    except urllib2.HTTPError as e:
        print e.code
        print e.read()
    except:
        print 'send json failed'
        exit(1)
    return response

# def get_lines(file,flop,cards):
#     lines = list()
#     with open(file, 'r') as f:
#         for v_line in f:
#             # get the line without varying turn or river card
#             default_line = util.get_default_line(v_line)
#             lines_per_default_line = util.generate_lines(default_line,flop,cards)
#             lines.extend(lines_per_default_line)
#         #print lines
#     return lines

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
            full_key = util.key2fullkey(flop,key,POT_TYPE,BET_SIZE)
            output_file = output_flop_dir + full_key + '.txt'
            output_files.append(output_file)
            if os.path.isfile(output_file):
                os.remove(output_file)
            content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
            content += 'show_strategy_pp ' + key + '\n'
            content += 'show_children ' + key + '\n'
        #print content
        f.write(content)
    return output_files, helper_script

def build_script_to_generate_results_all_keys_one_file(keys, value, flop, helpers_dir, output_dir):
    # make script per flop
    helper_script = helpers_dir + flop.name + '.txt'
    if os.path.isfile(helper_script):
        os.remove(helper_script)
    output_flop_dir = output_dir + flop.name + '\\'
    if not os.path.exists(output_flop_dir):
        os.makedirs(output_flop_dir)
    key_names = list()
    output_file = output_flop_dir + flop.name + '-' + str(value) + '.txt'
    with open(helper_script, 'w+') as f:
        content = 'load_tree ' + '"' + flop.path + '"' + '\n'
        content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
        for key in keys:
            if os.path.isfile(output_file):
                os.remove(output_file)
            content += 'stdoutredi_append ' + '"' + output_file + '"' + '\n'
            content += 'show_strategy_pp ' + key + '\n'
            content += 'show_children ' + key + '\n'
        #print content
        content += 'free_tree'+ '\n'
        f.write(content)
    return output_file, helper_script

def create_json(pio_results_file):
    #temp for testing
    with open(pio_results_file,'r+') as f:
        file = f.read()
        split_file = file.split('\n')
        #find lines with children and extract action
        actions,i = util.get_actions_and_end_of_file(split_file)
        json_content_of_key = util.build_json(split_file,actions,i)
    f.closed
    return json_content_of_key

def create_json2(pio_results_file,flop,subkeys):
    json_content = dict()
    with open(pio_results_file,'r+') as f:
        file = f.read()
        results_per_key = file.split("stdoutredi_append ok!")
        results_per_key = results_per_key[1:] #skip first line
        if (len(subkeys) == len(results_per_key)) == False:
            print 'ERROR: number of found keys in Pio results file is not equal to keys (requires debugging)'
        for i,result in enumerate(results_per_key):
            subkey = subkeys[i]
            split_file = result.split('\n')
            #find lines with children and extract action
            actions,index = util.get_actions_and_end_of_file(split_file)
            # generate full key
            full_key_corr = util.key2fullkey(flop, subkey, POT_TYPE, BET_SIZE)
            #make json content and add to dict
            json_content_of_key = util.build_json(split_file,actions,index)
            json_content[full_key_corr] = json_content_of_key
    f.closed
    return json_content

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
    json_dir = os.path.join(work_dir,'json_files')+'\\'
    #json_dir = JSON_DIR
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

def init_program(path_app,global_vars):
    ##initialize all global variables
    global FLOP_FOLDER, RESULTS_FOLDER, MAIN_FOLDER, FLOP_DIR, \
        RESULTS_DIR, JSON_DIR, PROCESSED_FLOPS_DIR, STEP_SIZE, FLOP_LOCAL_INPUT_FOLDER, \
        FLOP_LOCAL_RESULTS_FOLDER, MOVE_RESULTS, MAKE_JSON, SEND_JSON, REMOVE_JSON_AFTER_SENDING_DB, \
        REMOVE_PIO_OUTPUTS, LOG_SOLVED_FLOPS, MOVE_PROCESSED_FLOPS, LOG_NAME, POT_TYPE, BET_SIZE
    ## appoint values to global variables:
    # Locations
    FLOP_FOLDER = global_vars['FLOP_FOLDER']  # for input folder in main folder
    RESULTS_FOLDER = global_vars['RESULTS_FOLDER']
    MAIN_FOLDER = global_vars['MAIN_FOLDER']
    FLOP_DIR = global_vars['FLOP_DIR']  # for input folder full path
    RESULTS_DIR = global_vars['RESULTS_DIR']  # or set to local folder 'OUTPUT_results'
    JSON_DIR = global_vars['JSON_DIR']  # folder where jsons are saved
    PROCESSED_FLOPS_DIR = global_vars['PROCESSED_FLOPS_DIR']
    # Settings for solving:
    STEP_SIZE = global_vars['STEP_SIZE']  # number of keys retrieved in one Pio command
    FLOP_LOCAL_INPUT_FOLDER = global_vars['FLOP_LOCAL_INPUT_FOLDER']  # if true local disk is used for flop inputs
    FLOP_LOCAL_RESULTS_FOLDER = global_vars['FLOP_LOCAL_RESULTS_FOLDER']  # if true local disk is used for pio output results files
    MOVE_RESULTS = global_vars['MOVE_RESULTS']  # copy results from local folder to external folder
    MAKE_JSON = global_vars['MAKE_JSON']
    SEND_JSON = global_vars['SEND_JSON']
    REMOVE_JSON_AFTER_SENDING_DB = global_vars['REMOVE_JSON_AFTER_SENDING_DB']
    REMOVE_PIO_OUTPUTS = global_vars['REMOVE_PIO_OUTPUTS']
    LOG_SOLVED_FLOPS = global_vars['LOG_SOLVED_FLOPS']
    MOVE_PROCESSED_FLOPS = global_vars['MOVE_PROCESSED_FLOPS']
    LOG_NAME = global_vars['LOG_NAME']
    # Tree properties (used in Pio solver):
    POT_TYPE = global_vars['POT_TYPE']  # 3bet = 3, 4bet = 4, single raised pot = s
    BET_SIZE = global_vars['BET_SIZE']  # x big blind (e.g. 2.5 or 4)
    ##start core program
    get_results(path_app)
    return

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