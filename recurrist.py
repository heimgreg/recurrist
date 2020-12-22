#!/usr/bin/env python3
import sys
from datetime import datetime, timezone
from os import environ
from wrapper import TodoistWrapper


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


def recreate_completed_tasks():
    pass


def main():
    try:
        wrapper = init()
    except Exception:
        sys.exit(1)
    completed = wrapper.get_completed_items_since(
            datetime(2020, 12, 7, tzinfo=timezone.utc))
    task = wrapper.get_task_details(completed[1]["task_id"])
    print(task)
    label = wrapper.get_label_details(task["labels"][0])
    print(label)


if __name__ == '__main__':
    sys.exit(main())
