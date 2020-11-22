#!/usr/bin/python3

import sys
sys.path.append('.')
from wrapper import *
from os import environ

def getTodoistToken():
    token = environ.get('TODOIST_TOKEN')
    if token == None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token

def getTodoistWrapper(token):
    wrapper = None
    try:
        wrapper = TodoistWrapper(token)
    except:
        raise

def init():
    try:
        token = getTodoistToken()
        wrapper = getTodoistWrapper(token)
    except Exception as e:
        print("Error while initializing Recurrist")
        raise

def main():
    try:
        init()
    except:
        quit()

if __name__ == '__main__':
    sys.exit(main())
