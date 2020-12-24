#!/usr/bin/env python3

"""Automation for Todoist.

With this module, tasks in Todoist can be
* recreated after completion for recurring tasks without due dates,
* updated automatically.
"""

import sys
import json
from os import environ
from datetime import datetime
from wrapper import TodoistWrapper


__config = {}
__wrapper = None


def load_config():
    """Load configuration from config file config.json."""
    global __config
    with open("config.json", "r") as config_file:
        __config = json.load(config_file)


def get_todoist_token():
    """Load Todoist API token from environment variable TODOIST_TOKEN."""
    token = environ.get('TODOIST_TOKEN')
    if token is None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token


def init():
    """Initialize Recurrist."""
    global __wrapper
    try:
        token = get_todoist_token()
        __wrapper = TodoistWrapper(token)
        load_config()
    except Exception as e:
        print("Error while initializing Recurrist: " + str(e))
        raise


def read_time_of_last_run():
    """Read timestamp of last run from file."""
    content = None
    try:
        with open("lastrun.json", "r") as fh:
            content = json.load(fh)
    except Exception:
        pass
    if content is not None:
        return datetime.fromisoformat(content['last_run'])
    return None


def write_time_of_last_run(time):
    """Write timestamp of current run to file."""
    isinstance(time, datetime)
    content = {}
    content['last_run'] = time.isoformat()
    with open("lastrun.json", "w") as fh:
        json.dump(content, fh)


def recreate_completed_tasks():
    """Recreate task that were completed since last run."""
    last_run = read_time_of_last_run()
    current_time = datetime.utcnow()
    completed = __wrapper.get_completed_items_since(last_run)
    print(completed)
    write_time_of_last_run(current_time)
    pass


def update_tasks():
    """Update tasks if a trigger matches."""
    pass


def main():
    """Recurrist's main function."""
    # try:
    #     wrapper = init()
    # except Exception:
    #     sys.exit(1)
    # global __config

    init()
    recreate_completed_tasks()
    update_tasks()


if __name__ == '__main__':
    sys.exit(main())
