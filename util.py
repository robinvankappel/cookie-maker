__author__ = 'Robin'

import os
import time
import psutil
import sys
import json
import bz2

#todo: corresponds to pot type --> make settings file (git ignore) which include these
###GLOBAL VARIABLES###
POTSIZEMAX = 2000
POTSIZESTART = 200 #if POT_TYPE = 3
#POTSIZESTART = 50 #if POT_TYPE = s

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

def get_new_process(process_list,process_name,timeout=998,only_print_once=1):
    new_process_list = list()
    for proc in psutil.process_iter():
        if proc.name() == process_name:
            new_process_list.append(proc)
    if (timeout <= 0):
        print 'failed in finding new process'
        exit(1)
    if (len(new_process_list)>len(process_list)):
        new_process = list(set(new_process_list) - set(process_list))#get new process
        if len(new_process)>1:
            if only_print_once == 1:
                print 'ERROR: multiple new processes found'
                only_print_once = 0
            return get_new_process(process_list, process_name, timeout - 1, only_print_once)
        else:
            return new_process[0];
    else:
        time.sleep(1)
        return get_new_process(process_list,process_name, timeout - 1)

def getTime(start,flop):
    time_new = time.time()
    time_str = '(Time: ' + str(int(time_new - start)) + 's, ' + flop.name + ') '
    return time_str

def key2fullkey(flop,key,pot_type,bet_size):
    full_key = flop.name + '_' + str(pot_type) + '_' + str(int(bet_size * 10.0)) + '_' + key.replace(':', '_')
    return full_key

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
            name = file.split('.')[0]
            path = flop_dir + file
            flops.append(Flop(name,flop_dir,path))
    return flops

def FileWriteIsDone(path, filesize=None, timeout=1999):
    sys.stdout.write('\r'+str(timeout))
    sys.stdout.flush()
    if (timeout <= 0):
        return False
    if (os.path.isfile(path)):
        filesize_new = os.stat(path).st_size
        if (filesize_new == filesize) and (filesize > 10000):
            return True;
        else:
            time.sleep(1)
            return FileWriteIsDone(path, filesize_new, timeout - 1)
    else:
        time.sleep(1)
        return FileWriteIsDone(path,filesize,timeout - 1)

def FileWriteIsDone2(path, str_identifier, timeout=1999):
    sys.stdout.write('\r' + str(timeout))
    sys.stdout.flush()
    if (timeout <= 0):
        return False
    #a = win32gui.FindWindow(None, 'C:\Windows\system32\cmd.exe')
    #print(a, os.path.isfile(path))
    #check whether file exists and is not empty
    if (os.path.isfile(path) and (str_identifier in open(path).read())):
        return True;
    else:
        time.sleep(1)
        return FileWriteIsDone2(path,str_identifier,timeout - 1)

def DirWriteIsDone(dir, timeout=999):
    if (timeout <= 0):
        return False
    if os.path.exists(dir):
        return True
    else:
        time.sleep(1)
        return FileWriteIsDone(dir, timeout - 1)

def BatchWriteIsDone(path, timeout=999):
    if (timeout <= 0):
        return False
    #a = win32gui.FindWindow(None, 'C:\Windows\system32\cmd.exe')
    #print(a, os.path.isfile(path))
    #check whether file exists and is not empty
    if (os.path.isfile(path) and ('.txt' in open(path).read())):
        return True;
    else:
        time.sleep(1)
        return FileWriteIsDone(path, timeout -1)

# def print_output_error_Popen(p):
#     out, err = p.communicate()
#     if err:
#         print 'Error Popen: '
#         print err
#     if out:
#         print 'Output Popen: '
#         print out
#     return

def build_json(file,actions,i):
    # get results between first line and empty line
    file_results = file[1:i-2]
    json_content_of_key = {}
    json_content_of_key.update({'sizings':actions})
    for i,line in enumerate(file_results):
        hand = line.split(':')[0]
        line2 = filter(None,line.split(' '))[1:]
        values = [int(round(float(x)*100)) for x in line2]
        json_content_of_key.update({str(hand):values})
    # compress:
    #json_content_of_key = bz2.compress(json_content_of_key)
    return json_content_of_key

class Flop():
    """
    Make object containing filename and starttime
    """
    def __init__(self, name, dir, path):
        self.name = name
        self.dir = dir
        self.path = path

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

def get_keys_from_file(line_file,flop,cards):
    all_keys = list()
    #retrieve keys from line file
    keys_without_cards = get_keys_without_cards(line_file)

    for key in keys_without_cards:
        # add turn and river card in correct positions
        default_line = add_turn_and_river_cards(key)

        # OMIT LINES if:
        #   lines ending on f
        #   c:c after river
        #   c after b after river
        #   keys which are all-in
        all_in_situation = 'b' + str(int((POTSIZEMAX - POTSIZESTART) / 2)) + ':c'
        if (default_line[-1] == 'f') or \
                ('river' in default_line and default_line.endswith('c:c')) or \
                ('river' in default_line and default_line.endswith(':c') and default_line[-(len(':c') + 1)].isdigit()):
            continue
        elif (key.endswith(all_in_situation)):
            print 'skipped key because of all-in: ' + key
            continue

        # add cards
        lines_per_default_line = add_cards(default_line, flop, cards)
        all_keys.extend(lines_per_default_line)
    return all_keys

def add_cards(default_line,flop,all_cards):
    lines = list()
    if 'turn' in default_line:
        #exclude flop cards
        card1 = flop.name[0:2]
        card2 = flop.name[2:4]
        card3 = flop.name[4:6]
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

def add_subkeys_and_metadata_to_output(subkeys,pio_results_output,pot_type,bet_size):
    #append keys to existing file
    content = '\n' + 'KEYS START' + '\n'
    with open(pio_results_output, 'a') as f:
        #add keys
        for subkey in subkeys:
            content += subkey + '\n'
        content += 'KEYS END' + '\n'
        #add meta data
        content += 'POT_TYPE:'+ '\n'
        content += pot_type + '\n'
        content += 'BET_SIZE:' + '\n'
        content += str(bet_size) + '\n'
        f.write(content)
    return

# def generate_lines(default_line,flop,all_cards):
#     if 'turn' in default_line:
#         lines = list()
#         #exclude flop cards
#         card1 = flop.name[0:2]
#         card2 = flop.name[2:4]
#         card3 = flop.name[4:6]
#         cards = all_cards[0:len(all_cards)]
#         try:
#             cards.remove(card1)
#         except:
#             print 'FAIL: generating lines including all turn and river cards (function generate_lines)'
#         cards.remove(card2)
#         cards.remove(card3)
#         # loop over turn and river cards, excluding already existing turn card
#         for turn_card in cards:
#             river_cards = cards[0:len(cards)]
#             river_cards.remove(turn_card)
#             for river_card in river_cards:
#                 new_line = default_line
#                 new_line = new_line.replace('turn',turn_card)
#                 new_line = new_line.replace('river',river_card)
#             lines.append(new_line)
#     return lines

