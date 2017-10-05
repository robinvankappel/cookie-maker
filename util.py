__author__ = 'Robin'

import os
import time
import psutil
import sys
from config_paths import *

def kill_all_processes(process):
    for proc in psutil.process_iter():
        if proc.name() == process:
            proc.terminate()
    return

def get_all_processes(process):
    process_list = list()
    for proc in psutil.process_iter():
        if proc.name() == process:
            process_list.append(proc)
    return process_list

#Wait till new process is found. If timeout = -1, iteration never stops
def get_new_process(process_list,process_name,timeout=-1,only_print_once=1):
    while 1:
        new_process_list = list()
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                new_process_list.append(proc)
        if (timeout == 0):
            print 'failed in finding new process'
            exit(1)
        if (len(new_process_list)>len(process_list)):
            new_process = list(set(new_process_list) - set(process_list))#get new process
            if len(new_process)>1:
                if only_print_once == 1:
                    print 'ERROR: multiple new processes found'
                    only_print_once = 0
                timeout -= 1
            else:
                return new_process[0];
        else:
            time.sleep(1)
            timeout -= 1

def getTime(flop):
    time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    time_str = '(Time: ' + time_now + ', ' + flop.flop + ') '
    return time_str

def wait_till_copy_finished(new_flop_path):
    copying = True
    size2 = -1
    while copying:
        size = os.path.getsize(new_flop_path)
        if size == size2:
            break
        else:
            size2 = size
            time.sleep(2)
    return

def get_flops(flop_dir):
    flops = list()
    for file in os.listdir(flop_dir):
        if file.endswith(".cfr"):
            filename = file.split('.')[0]
            stacksize = int(float(filename.split('_')[0]))
            type = filename.split('_')[1]
            flopname = filename.split('_')[2]
            path = flop_dir + file
            if not type == 's' and not '3' and not '4' and not '5' \
                    or len(flopname) != 6 \
                    or not isinstance(stacksize,int):
                print 'not a valid flop name: ' + str(file)
                continue
            flop = Flop(stacksize,type,flopname,flop_dir,path,filename)
            Flop.add_settings(flop)
            flops.append(flop)
    return flops

def FileWriteIsDone(path, filesize=None, timeout=-1):
    while 1:
        sys.stdout.write('\r'+str(abs(timeout)))
        sys.stdout.flush()
        if (timeout == 0):
            return False
        if (os.path.isfile(path)):
            filesize_new = os.stat(path).st_size
            if (filesize_new == filesize) and (filesize > 2000):
                time.sleep(3)#time to close file, might be necessary (?)
                return True;
            else:
                time.sleep(1)
                timeout -= 1
                filesize = filesize_new
        else:
            time.sleep(1)
            timeout -= 1

def BatchWriteIsDone(path, timeout=-1):
    while 1:
        if (timeout == 0):
            return False
        #check whether file exists and is not empty
        if (os.path.isfile(path) and ('.txt' in open(path).read())):
            return True;
        else:
            time.sleep(1)
            timeout -= 1

class Flop():
    """
    Make object containing filename and starttime
    """
    def __init__(self, stacksize, type, flop, dir, path, filename):
        self.stacksize = stacksize
        self.type = type
        self.flop = flop
        self.dir = dir
        self.path = path
        self.filename = filename
    def add_settings(self):
        self.settings = Settings(self)

def generate_watch_folders(i,output_dir_base,numberofwatchfolders=1):
    if (i % numberofwatchfolders) == 0:
        output_dir = os.path.join(output_dir_base, 'A')
    elif (i % numberofwatchfolders) == 1:
        output_dir = os.path.join(output_dir_base, 'B')
    elif (i % numberofwatchfolders) == 2:
        output_dir = os.path.join(output_dir_base, 'C')
    elif (i % numberofwatchfolders) == 3:
        output_dir = os.path.join(output_dir_base, 'D')
    elif (i % numberofwatchfolders) == 4:
        output_dir = os.path.join(output_dir_base, 'E')
    elif (i % numberofwatchfolders) == 5:
        output_dir = os.path.join(output_dir_base, 'F')
    elif (i % numberofwatchfolders) == 6:
        output_dir = os.path.join(output_dir_base, 'G')
    elif (i % numberofwatchfolders) == 7:
        output_dir = os.path.join(output_dir_base, 'H')
    elif (i % numberofwatchfolders) == 8:
        output_dir = os.path.join(output_dir_base, 'I')
    elif (i % numberofwatchfolders) == 9:
        output_dir = os.path.join(output_dir_base, 'J')
    return output_dir

def get_pokercards():
    cards = list()
    #['c','h','s','d'], ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    for suit in ['c','h','s','d']:
        for value in ['2','3','4','5','6','7','8','9','T','J','Q','K','A']:
            card = value+suit
            cards.append(card)
    return cards

def convert_situation_to_filename(situation):
    situation_conv = situation.replace(':', '_')
    return situation_conv

#read line, extract all possible keys of that line and store.
# also add per key the actions (bet66, raise172, call, check, fold)
def get_keys(lines):
    #r:0|:c|:c:3d|:c|:c:8d|:c|:b25|:b100|:b262|:b975
    #everywhere except after 2nd c if two cc next to each other.
    keys = list()
    for line in lines:
        line_split = line.split(':')
        for i,action in enumerate(line_split):
           #omit first element
           if not i == 0 and not i == 1:
                #if two elements are the same (c:c) then omit making a new key
                if not action == line_split[i-1]:
                    new_key = ':'.join(line_split[0:i])
                    keys.append(new_key)
    return keys

def get_keys_from_file(flop,linefile,cards=get_pokercards()):
    all_keys = list()
    #retrieve keys from line file
    keys_without_cards = get_keys_without_cards(linefile)

    for key in keys_without_cards:
        # add turn and river card in correct positions
        default_line = add_turn_and_river_cards(key)

        # OMIT LINES if:
        #   lines ending on f
        #   c:c after river
        #   c after b after river
        #   keys which are all-in
        all_in_situation = 'b' + str(int((flop.settings.POTSIZEMAX - flop.settings.POTSIZESTART) / 2)) + ':c'
        if (default_line[-1] == 'f') or \
                ('river' in default_line and default_line.endswith('c:c')) or \
                ('river' in default_line and default_line.endswith(':c') and default_line[-(len(':c') + 1)].isdigit()):
            continue
        elif (key.endswith(all_in_situation)):
            #print 'skipped key because of all-in: ' + key
            continue

        # add cards
        lines_per_default_line = add_cards(default_line, flop, cards)
        all_keys.extend(lines_per_default_line)
    return all_keys

def add_cards(default_line,flop,all_cards):
    lines = list()
    if 'turn' in default_line:
        #exclude flop cards
        card1 = flop.flop[0:2]
        card2 = flop.flop[2:4]
        card3 = flop.flop[4:6]
        cards = all_cards[0:len(all_cards)]
        try:
            cards.remove(card1)
        except:
            print 'FAIL: generating lines including all turn and river cards (function generate_lines)'
        cards.remove(card2)
        cards.remove(card3)
        # loop over turn and river cards, excluding already existing turn card
        # if only turn card exists
        if 'turn' and not 'river' in default_line:
            for turn_card in cards:
                new_line = default_line
                new_line = new_line.replace('turn',turn_card)
                lines.append(new_line)
        # if both turn and river card exist
        elif 'turn' and 'river' in default_line:
            for turn_card in cards:
                river_cards = cards[0:len(cards)]
                river_cards.remove(turn_card)
                for river_card in river_cards:
                    new_line = default_line
                    new_line = new_line.replace('turn',turn_card)
                    new_line = new_line.replace('river',river_card)
                    lines.append(new_line)
    else:
        lines.append(default_line)
    return lines

def add_turn_and_river_cards(key):
    actions = key.split(":")
    # 0 = c
    # if i=i+1 then a turn card follows
    # if again i=i+1 then river card follows
    action_prev = 'random_initiator'
    for i, action in enumerate(actions):
        #if c:c or if bX:c
        if (action == action_prev) or (action == 'c' and action_prev[1:].isdigit()):
            # if not action == actions[i-1] and not action[i-1] == actions[i-2]:
            if 'turn' and 'river' in actions:
                continue
            elif 'turn' in actions:
                actions.insert(i+1, 'river')
            else:
                actions.insert(i+1, 'turn')
        action_prev = action
    line = ':'.join(actions)
    return line

def get_actions_and_end_of_file(file):
    actions = list()
    already_detected = 0
    for i,line in enumerate(file):
        #get actions and bet sizes
        if "child " in line:
            next_line = file[i+1]
            next_line_split = next_line.split(':')
            #if c is not after a bet, it must be a check
            last_element = next_line_split[-1]
            if last_element == 'c' and not next_line_split[-2].startswith('b'):
                actions.append('x')#k = check
            elif last_element == 'c':
                actions.append('c')#c = check
            elif last_element.startswith('b'):
                actions.append(last_element[1:])#only bet size, without the b
            elif last_element == 'f':
                actions.append(last_element)#f = fold
            else:
                'unrecognised element as action in children'
                exit()
        #get first END word to get part of file with results
        elif line == 'END' and already_detected == 0:
            end_of_file_index = i-1
            already_detected = 1
    return actions, end_of_file_index

def get_keys_without_cards(file):
    lines = list()
    with open(file, 'r') as f:
        for v_line in f:
            if v_line.startswith('r:0'):
                # get the line without varying turn or river card
                line = v_line.split(" ")[0]
                lines.append(line)
        #print lines
    return lines

class Key():
    """
    Make object with key value (e.g. r:0:b66) and key actions (e.g.bet66, raise172, call, check, fold)
    """
    def __init__(self, key_value, key_actions):
        self.value = key_value
        self.actions = key_actions

def get_default_line(v_line):
    actions = v_line.split(" ")
    # 0 = c
    # if i=i+1 then an turn card follows
    # if again i=i+1 then river card follows
    action_prev = 'random_initiator'
    line = ''
    for i, action in enumerate(actions):
        if action == '0':
            action = 'c'
        if action == action_prev:
            # if not action == actions[i-1] and not action[i-1] == actions[i-2]:
            action = 'c'
            if 'turn' in actions:
                actions.insert(i+1, 'river')
            else:
                actions.insert(i+1, 'turn')
        action_prev = action
        if not action.isalpha() and not i == 0:
            action = 'b' + action
        if i == len(actions)-1:
            line += action.split("\n")[0]
        elif i == 0:
            line += 'r:0:'
        else:
            line += action + ':'
    return line

def add_subkeys_and_metadata_to_output(subkeys,pio_results_output,flop):
    content = '\n' + 'END_OF_RESULTS' + '\n'
    with open(pio_results_output, 'a') as f:
        # append keys to existing file
        content += '\n' + 'KEYS START' + '\n'
        #add keys
        for subkey in subkeys:
            content += subkey + '\n'
        content += 'KEYS END' + '\n'
        #add meta data
        content += 'POT_TYPE:'+ '\n'
        content += flop.type + '\n'
        content += 'BET_SIZE:' + '\n'
        content += str(flop.stacksize) + '\n'
        content += 'END_OF_FILE' + '\n'
        f.write(content)
    while 1:
        if f.closed:
            return
        # else:
        #     time.sleep(1)

class PioOutput():
    """
    Make object containing filename and starttime
    """
    def __init__(self, output_file,keys):
        self.file = output_file
        self.keys = keys

def run_in_powershell(batch_path):
    command = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command "& { Start-Process ' + batch_path + ' -verb RunAs}"'
    return command


