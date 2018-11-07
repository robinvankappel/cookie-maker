__author__ = 'RvK'

import util
import shutil
#import sys
#sys.path.append('D:\cookie')
import itertools
import time
import subprocess
from config_maker import *
#from config_cookie import *


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
def cookie_maker(path_app):

    #get/define all folder locations to be used
    output_dir, helpers_dir, lines_dir = get_dirs(path_app)
    watchers = Watchers(WATCHERS,WATCH_DIR)
    print 'Starting with processing flops in input folder...'

    # get all flop files
    flops = util.get_flops(FLOP_DIR)
    #iterate over flops in dir
    for flop in flops:
        flop_start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print util.getTime(flop) + 'flop: ' + str(flop.flop) + ', type: ' + flop.type + ', stack size: ' + str(flop.stacksize)
        log_flops(flop, LOG_FILE, flop_start_time)

        # save original flop location
        flop_path_original = flop.path

        #GENERATE KEYS FROM FILE WITH ALL LINES WITHOUT TURN AND RIVER CARDS
        keys = get_all_keys(flop,lines_dir,helpers_dir)
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

        # make script per flop
        helper_script = helpers_dir + flop.flop + '.txt'
        if os.path.isfile(helper_script):
            os.remove(helper_script)

        # initialize pio script
        print util.getTime(flop) + 'building script for Pio...'
        with open(helper_script, 'w+') as f:
            content = 'load_tree ' + '"' + flop.path + '"' + '\n'
            f.write(content)
        pio_outputs = list()
        # iterate over subset of keys such that entire process is split in parts, for computational reasons.
        keys_iter = make_subset_keys(flop.settings.STEP_SIZE, keys)
        for i,subset_end_index in enumerate(keys_iter):
            #add subkeys to script
            if not i == 0:
                # use different output folders such that multiple watchers can be used:
                output_dir = watchers.paths[i % watchers.number]

                subkeys = keys[keys_iter[i-1]:keys_iter[i]]

                # add subkeys with subfolder to pio script which can generate the results for these keys incl. actions (=children)
                pio_output = build_script_to_generate_results_all_keys_one_file(subkeys, subset_end_index,
                                                                                                      flop,helper_script,output_dir,end=(i==len(keys_iter)-1))
                pio_outputs.append(pio_output)

        #build batch and run batch to start pio
        new_pio_process = run_pio(flop, helper_script, helpers_dir)

        # print util.getTime(flop) + 'Adding subkeys and meta-data to each output file...'
        # # add subkeys to each output file:
        # for pio_output in pio_outputs:
        #     if (util.FileWriteIsDone(pio_output.file)):
        #         util.add_subkeys_and_metadata_to_output(pio_output.keys, pio_output.file, flop)

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
        log_flops(flop, LOG_FILE, flop_end_time, outputs=len(pio_outputs), keys=keys, avg_length=avg_length, max_length=max_length, finished=1)

        if MOVE_PROCESSED_FLOPS:
            print util.getTime(flop) + 'move processed flop'
            #move processed flop to different folder:
            path,file = os.path.split(flop_path_original)
            try:
                os.rename(flop_path_original, os.path.join(PROCESSED_FLOPS_DIR,file))
            except:
                print util.getTime(flop) + 'ERROR: could not move flop as it already exist in destination folder'
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

def get_all_keys(flop,lines_dir,helpers_dir):
    if os.path.isfile(lines_dir + flop.settings.LINEFILE):
        # select linefile based on flop type and stack size
        keys = util.get_keys_from_file(flop,lines_dir)
        print util.getTime(flop) + 'Retrieved all keys from ' + flop.settings.LINEFILE
    else:
        print util.getTime(flop) + 'Starting proces to generate lines...'
        # uncomment line below to generate script to retrieve lines, then run script in Pio.
        line_script = build_script_to_get_lines(flop, lines_dir, helpers_dir)
        # build batch which runs the linefile
        batch_lines = build_batch_to_get_floplines(flop,line_script, helpers_dir)
        # run batch file to run the script in Pio which retrieves the lines
        if (util.BatchWriteIsDone(batch_lines)):
            existing_pio_processes = util.get_all_processes(PIO_NAME)
            #print util.getTime(flop) + 'Running Pio to retrieve lines...'
            if USE_POWERSHELL:
                command = util.run_in_powershell(batch_lines)
                q = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                q = subprocess.Popen(batch_lines, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #wait till new Pio process is started:
            new_pio_process = util.get_new_process(existing_pio_processes,PIO_NAME)
            #print util.getTime(flop) + 'corresponding Pio process found (PID:' + str(new_pio_process.pid) + ')'
        else:
            print util.getTime(flop) + 'FAILED opening batch file to get lines'
            exit(1)

        # get the keys from the file created by Pio
        if (util.FileWriteIsDone(flop.settings.LINE_FILE)):
            if os.stat(flop.settings.LINE_FILE).st_size < 2000:
                print util.getTime(flop) + 'failed getting lines (line file < 2KB)'
                exit(1)
            #print util.getTime(flop) + 'getting keys from lines...'
            keys = util.get_keys_from_file(flop,lines_dir)

            new_pio_process.terminate()
            time.sleep(2)#wait (longer than wait of sleep timer in get_new_process such that other process can continue)
            #util.kill_all_processes(PIO_NAME)
            print util.getTime(flop) + 'Retrieved all keys by generating them with Pio'
        else:
            print util.getTime(flop) + 'failed reading lines from file'
            exit(1)
    return keys

def copy_flop(flop,temp_flop_dir):
    print util.getTime(flop) + 'Copy flop to local disk...'
    shutil.copy2(flop.path, temp_flop_dir)  # copy flop to local disk
    new_flop_path = temp_flop_dir + flop.flop + '.cfr'  # set new flop as flop
    util.wait_till_copy_finished(new_flop_path)
    flop.path = new_flop_path  # set new flop as flop
    print util.getTime(flop) + 'finished copying'
    return new_flop_path

def log_flops(flop, log_file, time, outputs=None,keys=None, avg_length=None, max_length=None, finished=False):
    with open(log_file, 'a+') as f:
        if finished:
            content = 'FINISHED flop: ' + flop.flop + ', ' + str(flop.stacksize) + 'BB' + ', ' + flop.type + ' (' + time + ', ' + str(outputs) + 'files, ' + str(len(keys)) + ' keys, avg key length = ' + str(avg_length) + ', max key length = ' + str(max_length) + ')' + '\n'
        else:
            content = 'STARTING flop: ' + flop.flop + ', ' + str(flop.stacksize) + 'BB' + ', ' + flop.type + ' (' +  time + ', flop.STEP_SIZE = ' + str(flop.settings.STEP_SIZE) + ')' + '\n'
        f.write(content)
    return log_file

def build_batch_results_all_keys(flop,pio_results_file,helpers_dir):
    batch_file = helpers_dir + 'run_script_to_get_results' + flop.flop + '.bat'
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
    batch_file = helpers_dir + 'run_script_to_get_lines-' + flop.flop + '.bat'
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
    helper_script = helpers_dir + flop.flop + '_getlines.txt'
    if os.path.isfile(helper_script):
        os.remove(helper_script)
    output_file = lines_dir + flop.settings.LINEFILE
    #remove file if it already exists
    if os.path.isfile(output_file):
        os.remove(output_file)
    with open(helper_script, 'w+') as f:
        content = 'load_tree ' + '"' + flop.path + '"' + '\n'
        content += 'stdoutredi ' + '"' + output_file + '"' + '\n'
        content += 'show_all_freqs local ' + '\n'
        f.write(content)
    return helper_script

def build_script_to_generate_results_all_keys_one_file(keys, subset_end_index, flop, helper_script, output_dir, end=False):
    output_file = output_dir + '\\' + flop.filename + '-' + str(subset_end_index) + '.txt'
    if os.path.isfile(output_file):
        os.remove(output_file)
    with open(helper_script, 'a+') as f:
        content = 'stdoutredi ' + '"' + output_file + '"' + '\n'
        for key in keys:
            content += 'show_strategy_pp ' + key + '\n'
            content += 'show_children ' + key + '\n'
            content += 'is_ready\n'
        #Adding subkeys and meta-data to output file
        content += 'echo END_OF_RESULTS\n'
        # append keys to existing file
        content += 'echo KEYS_START\n'
        # add keys
        for key in keys:
            content += 'echo ' + key + '\n'
        content += 'echo KEYS_END\n'
        # add meta data
        content += 'echo POT_TYPE:\n'
        content += 'echo ' + flop.type + '\n'
        content += 'echo BET_SIZE(BB):\n'
        content += 'echo ' + str(flop.settings.BET_SIZE) + '\n'
        content += 'echo END_OF_FILE\n'
        #remove tree from RAM with last helper file
        if end:
            content += 'free_tree' + '\n'
        f.write(content)
    pio_output = util.PioOutput(output_file,keys)
    return pio_output

def get_dirs(path_app):
    helpers_dir = os.path.join(path_app,'temp')+'\\'
    output_dir = WATCH_DIR
    lines_dir = os.path.join(path_app, 'lines') + '\\'
    for dir in [helpers_dir, output_dir, lines_dir, PROCESSED_FLOPS_DIR]:
        if not os.path.exists(dir):
            os.makedirs(dir)
    return output_dir, helpers_dir, lines_dir

if __name__ == "__main__":
    PATH_APP = os.path.abspath(os.path.dirname(sys.argv[0]))
    cookie_maker(path_app=PATH_APP)