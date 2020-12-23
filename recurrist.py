#!/usr/bin/env python3

"""Automation for Todoist.

With this module, tasks in Todoist can be
* recreated after completion for recurring tasks without due dates,
* updated automatically.
"""

import sys
import json
from os import environ
from wrapper import TodoistWrapper


def get_config():
    """Load configuration from config file config.json."""
    config = {}
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config


def get_todoist_token():
    """Load Todoist API token from environment variable TODOIST_TOKEN."""
    token = environ.get('TODOIST_TOKEN')
    if token is None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token


def init():
    """Initialize Recurrist."""
    try:
        token = get_todoist_token()
        wrapper = TodoistWrapper(token)
        return wrapper
    except Exception as e:
        print("Error while initializing Recurrist: " + str(e))
        raise


def recreate_completed_tasks():
    """Recreate task that were completed since last run."""
    pass


def main():
    """Recurrist's main function."""
    # try:
    #     wrapper = init()
    # except Exception:
    #     sys.exit(1)

    config = get_config()
    print(config)


if __name__ == '__main__':
    sys.exit(main())
