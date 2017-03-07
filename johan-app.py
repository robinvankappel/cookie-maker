#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from main_functions import get_results
import os, sys

path_app = os.path.abspath(os.path.dirname(sys.argv[0]))
#path_app.replace(' ','" "')

def main():
    get_results(path_app)

if __name__ == "__main__":
    main()
