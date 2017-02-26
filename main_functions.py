__author__ = 'Robin'

import util
import shutil
import os
import itertools
import time
import subprocess

##### LOCAL PATHS #####
from config_paths import *


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
# Build json from results and send to API (in watcher)
"""
#todo: if tree name is wrong, script fails.
def get_results(path_app):

    #get/define all folder locations to be used
    flop_dir, temp_flop_dir, output_dir, lines_dir, helpers_dir, json_dir = get_dirs(path_app)
    output_dir_base = output_dir#when using multiple watchers
    #get all cards existing in poker
    cards = util.get_pokercards()
    print 'Starting with processing flops in input folder...'

    # get all flop files
    flops = util.get_flops(flop_dir)
    #iterate over flops in dir
    for flop in flops:
        flop_start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print util.getTime(flop) + 'flop: ' + str(flop.name)
        log_file = log_flops(flop, output_dir_base, flop_start_time, stepsize = STEP_SIZE, pot_type=POT_TYPE)

        # save original flop location
        flop_path_original = flop.path

        #Function to copy flop to local disk because of performance reasons
        if FLOP_LOCAL_INPUT_FOLDER == False:
            copy_flop(flop,temp_flop_dir)

        #GENERATE KEYS FROM FILE WITH ALL LINES WITHOUT TURN AND RIVER CARDS
        keys = get_all_keys(flop,lines_dir,helpers_dir,cards,generate_new_keys=GENERATE_NEW_KEYS)
        print util.getTime(flop) + 'Total number of keys to process: ' + str(len(keys))
        lengths = [len(i) for i in keys]
        max_length = max(lengths)
        avg_length = round(sum(lengths) / float(len(lengths)),1)
        print util.getTime(flop) + 'Max key length: ' + str(max_length) + " --> key: " + str(keys[lengths.index(max_length)])
        print util.getTime(flop) + 'Average key length: ' + str(avg_length)

        #For testing purposes (normally all keys are used)
        if KEY_MAX_INDEX < len(keys):
            keys = keys[KEY_MIN_INDEX:KEY_MAX_INDEX]#for testing purpose
        else:
            keys = keys[KEY_MIN_INDEX:]

        #make subset of keys such that entire process is split in parts, for computational reasons.
        keys_iter = make_subset_keys(STEP_SIZE, keys)

        # make script per flop
        helper_script = helpers_dir + flop.name + '.txt'
        if os.path.isfile(helper_script):
            os.remove(helper_script)

        # initialize pio script
        print util.getTime(flop) + 'building script for Pio...'
        with open(helper_script, 'w+') as f:
            content = 'load_tree ' + '"' + flop.path + '"' + '\n'
            f.write(content)
        pio_outputs = list()
        #iterate over subsets
        for i,subset_end_index in enumerate(keys_iter):
            #add subkeys to script
            if not i == 0:
                # use different output folders such that multiple watchers can be used:
                output_dir = util.generate_watch_folders(i,output_dir_base,numberofwatchfolders=10)

                subkeys = keys[keys_iter[i-1]:keys_iter[i]]

                # add subkeys with subfolder to pio script which can generate the results for these keys incl. actions (=children)
                pio_output = build_script_to_generate_results_all_keys_one_file(subkeys, subset_end_index,
                                                                                                      flop,helper_script,output_dir)
                pio_outputs.append(pio_output)
        #finalize pio script
        with open(helper_script, 'a+') as f:
            content = 'free_tree' + '\n'
            f.write(content)

        #build batch and run batch to start pio
        new_pio_process = run_pio(flop, helper_script, helpers_dir)

        print util.getTime(flop) + 'Adding subkeys and meta-data to each output file...'
        # add subkeys to each output file:
        for pio_output in pio_outputs:
            if (util.FileWriteIsDone(pio_output.file)):
                util.add_subkeys_and_metadata_to_output(pio_output.keys, pio_output.file, POT_TYPE, BET_SIZE)

        #wait till last pio_results_output file is written, then add subkeys and metadata
        print util.getTime(flop) + 'waiting till last file is written...'
        if (util.FileWriteIsDone(pio_outputs[-1].file)):
            new_pio_process.terminate()
            print util.getTime(flop) + 'Pio process terminated'

        ###FINALISE
        print util.getTime(flop) + 'finished processing flop'
        flop_end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        print util.getTime(flop) + 'add flop to log'
        #save in log file which flops are solved
        log_flops(flop, output_dir_base, flop_end_time, keys=keys, avg_length=avg_length, finished=1)
        if MOVE_RESULTS:
            path, file = os.path.split(log_file)
            shutil.copyfile(log_file,RESULTS_DIR+file)

        if MOVE_PROCESSED_FLOPS:
            print util.getTime(flop) + 'move processed flop'
            #move processed flop to different folder:
            path,file = os.path.split(flop_path_original)
            os.rename(flop_path_original, os.path.join(PROCESSED_FLOPS_DIR,file))

        if FLOP_LOCAL_INPUT_FOLDER == False:
            #delete (copied) flop on local disk
            print util.getTime(flop) + 'remove flop on local disk'
            os.remove(flop.path)
    return 0


def run_pio(flop, pio_results_file, helpers_dir):
    # build windows batch file to run Pio
    batch_results = build_batch_results_all_keys(flop, pio_results_file, helpers_dir)

    # run batch file to run the script in Pio which generates the results of all keys
    print util.getTime(flop) + 'Generating batch file to retrieve tree results...'
    if (util.BatchWriteIsDone(batch_results)):
        existing_pio_processes = util.get_all_processes(PIO_NAME)
        print util.getTime(flop) + 'running Pio to retrieve results...'
        if USE_POWERSHELL:
            command = util.run_in_powershell(batch_results)
            q = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            q = subprocess.Popen(batch_results, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # wait till new Pio process is started:
        new_pio_process = util.get_new_process(existing_pio_processes, PIO_NAME)
        print util.getTime(flop) + 'corresponding Pio process found (PID:' + str(new_pio_process.pid) + ')'
    else:
        print util.getTime(flop) + 'failed opening batch file to get results'
        exit(1)

    return new_pio_process

def make_subset_keys(step_size, keys):
    keys_iter = list()
    for key_iter in itertools.islice(range(len(keys) - 1), 0, len(keys), step_size):
        keys_iter.append(key_iter)
    keys_iter.append(len(keys) - 1)
    return keys_iter

def get_all_keys(flop,lines_dir,helpers_dir,cards,generate_new_keys=1):
    if not generate_new_keys:
        lines_path = os.path.join(lines_dir, LINES_FILE)
        keys = util.get_keys_from_file(lines_path, flop, cards, POTSIZEMAX, POTSIZESTART)
        print util.getTime(flop) + 'retrieved all keys from ' + lines_path
    else:
        # uncomment line below to generate script to retrieve lines, then run script in Pio.
        line_file, line_script = build_script_to_get_lines(flop, lines_dir, helpers_dir)
        # build batch which runs the line_file
        batch_lines = build_batch_to_get_floplines(flop,line_script, helpers_dir)
        # run batch file to run the script in Pio which retrieves the lines
        print util.getTime(flop) + 'Writing files for retrieving lines...'
        if (util.BatchWriteIsDone(batch_lines)):
            existing_pio_processes = util.get_all_processes(PIO_NAME)
            print util.getTime(flop) + 'Running Pio to retrieve lines...'
            if USE_POWERSHELL:
                command = util.run_in_powershell(batch_lines)
                q = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                q = subprocess.Popen(batch_lines, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #wait till new Pio process is started:
            new_pio_process = util.get_new_process(existing_pio_processes,PIO_NAME)
            print util.getTime(flop) + 'corresponding Pio process found (PID:' + str(new_pio_process.pid) + ')'
        else:
            print util.getTime(flop) + 'failed opening batch file to get lines'
            exit(1)

        # get the keys from the file created by Pio
        if (util.FileWriteIsDone(line_file)):
            if os.stat(line_file).st_size < 10000:
                print util.getTime(flop) + 'failed getting lines (line file < 10KB)'
                exit(1)
            print util.getTime(flop) + 'getting keys from lines...'
            keys = util.get_keys_from_file(line_file, flop, cards, POTSIZEMAX, POTSIZESTART)

            new_pio_process.terminate()
            time.sleep(2)#wait (longer than wait of sleep timer in get_new_process such that other process can continue)
            #util.kill_all_processes(PIO_NAME)
            print util.getTime(flop) + 'retrieved all keys by generating them with Pio'
        else:
            print util.getTime(flop) + 'failed reading lines from file'
            exit(1)
    return keys

def copy_flop(flop,temp_flop_dir):
    print util.getTime(flop) + 'Copy flop to local disk...'
    shutil.copy2(flop.path, temp_flop_dir)  # copy flop to local disk
    new_flop_path = temp_flop_dir + flop.name + '.cfr'  # set new flop as flop
    util.wait_till_copy_finished(new_flop_path)
    flop.path = new_flop_path  # set new flop as flop
    print util.getTime(flop) + 'finished copying'
    return new_flop_path

def log_flops(flop, output_dir, time, keys=None, avg_length=None, stepsize=None, finished=False, pot_type=None):
    log_file = os.path.join(output_dir,LOG_NAME)
    with open(log_file, 'a+') as f:
        if finished:
            content = 'FINISHED flop: ' + flop.name + ' (' + time + ', ' + str(len(keys)) + ' keys, avg key length = ' + str(avg_length) + ')' + '\n'
        else:
            content = 'STARTING flop: ' + flop.name + ' (' +  time + ', step_size = ' + str(stepsize) + ', pot_type = ' + pot_type + ')' + '\n'
        f.write(content)
    return log_file

def build_batch_results_all_keys(flop,pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results' + flop.name + '.bat'
    if os.path.isfile(batch_file):
        os.remove(batch_file)
    with open(batch_file, 'w+') as f:
        content = 'set root=' + PIO_DIR + '\n'
        content += 'cd %root%' + '\n'
        content += 'start /min ' + PIO_LOC + ' "' + pio_results_file + '"\n'
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
        content += 'start /min ' + PIO_LOC + ' "' + pio_lines_file + '"\n'
        # print 'Script for getting results of Pio'
        # print content
        # print '\n'
        f.write(content)
    return batch_file

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

def build_script_to_generate_results_all_keys_one_file(keys, subset_end_index, flop, helper_script, output_dir):
    output_file = output_dir + '\\' + flop.name + '-' + str(subset_end_index) + '.txt'
    with open(helper_script, 'a+') as f:
        content = 'stdoutredi ' + '"' + output_file + '"' + '\n'
        for key in keys:
            if os.path.isfile(output_file):
                os.remove(output_file)
            content += 'show_strategy_pp ' + key + '\n'
            content += 'show_children ' + key + '\n'
            content += 'is_ready' + '\n'
        f.write(content)
    pio_output = util.PioOutput(output_file,keys)
    return pio_output

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
