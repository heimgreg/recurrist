#!/usr/bin/env python3
import sys
from os import environ
sys.path.append('.')
#pylint: disable=wrong-import-position
from wrapper import TodoistWrapper
#pylint: enable=wrong-import-position

def get_todoist_token():
    """ Load Todoist API token from environment variable TODOIST_TOKEN """
    token = environ.get('TODOIST_TOKEN')
    if token is None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token

def get_todoist_wrapper(token):
    wrapper = TodoistWrapper(token)
    return wrapper

def init():
    try:
        token = get_todoist_token()
        wrapper = get_todoist_wrapper(token)
        return wrapper
    except Exception as e:
        print("Error while initializing Recurrist: " + str(e))
        raise

def main():
    try:
        wrapper = init()
    except:
        sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())
