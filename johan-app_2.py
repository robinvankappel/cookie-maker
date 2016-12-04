#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from main_functions_2 import get_results2
import os, sys

path_app = os.path.abspath(os.path.dirname(sys.argv[0]))

def main():
    # parse command line options
    # try:
    get_results2(path_app)
    # except:
    #     print "main function failed"

if __name__ == "__main__":
    main()
