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
from todoist.api import TodoistAPI
from jsonschema import validate


__config = {}
__todoist = None
__dry = True


def load_config():
    """Load configuration from config file config.json."""
    global __config
    schemafile = open("config.schema", "r")
    schema = json.load(schemafile)
    schemafile.close()
    filename = "config.json"
    print("Loading configuration file " + filename)
    with open(filename, "r") as config_file:
        __config = json.load(config_file)
    try:
        validate(schema, __config)
        print("Successfully checked format of configuration file.")
    except Exception as e:
        print("Invalid configuration format: " + e.message)
        raise


def replace_names_in_config():
    """Find labels and projects and store them.

    The string from the configuration are replaced by
    their equivalent todoist objects.
    """
    def unknown_label(name):
        raise Exception("Unknown label '" + name + "' in configuration!")

    def unknown_project(name):
        raise Exception("Unknown project '" + name + "' in configuration!")

    for task in __config["tasks"]:
        if "labels" in task["filter"].keys():
            for i in range(len(task["filter"]["labels"])):
                label = find_label_by_name(task["filter"]["labels"][i])
                if label is None:
                    unknown_label(task["filter"]["labels"][i])
                task["filter"]["labels"][i] = label
        if "project" in task["filter"].keys():
            project = find_project_by_name(task["filter"]["project"])
            if project is None:
                unknown_project(task["filter"]["project"])
            task["filter"]["project"] = project
        for action in task["actions"]:
            if "add_label" in action["action"].keys():
                label = find_label_by_name(action["action"]["add_label"])
                if label is None:
                    unknown_label(action["action"]["add_label"])
                action["action"]["add_label"] = label
        if "skip_label_on_recreate" in task.keys():
            label = find_label_by_name(task["skip_label_on_recreate"])
            if label is None:
                unknown_label(task["skip_label_on_recreate"])
            task["skip_label_on_recreate"] = label


def find_label_by_name(name):
    """Find label by its name."""
    label = __todoist.labels.all(lambda x: x["name"] == name)
    return label[0] if len(label) > 0 else None


def find_project_by_name(name):
    """Find project by its name."""
    project = __todoist.projects.all(lambda x: x["name"] == name)
    return project[0] if len(project) > 0 else None


def get_todoist_token():
    """Load Todoist API token from environment variable TODOIST_TOKEN."""
    token = environ.get('TODOIST_TOKEN')
    if token is None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token


def connect(token):
    """Connect to Todoist API."""
    global __todoist
    print("Connecting to Todoist API")
    __todoist = TodoistAPI(token)
    try:
        syncres = __todoist.sync()
        if 'error' in syncres:
            raise Exception(syncres["error"])
        print("Successfully synced with Todoist")
    except Exception as e:
        print("Failed to sync with todoist: " + str(e))
        raise


def init():
    """Initialize Recurrist."""
    print("Starting initialization")
    try:
        load_config()
        token = get_todoist_token()
        connect(token)
        replace_names_in_config()
    except Exception as e:
        print("Error while initializing Recurrist: " + str(e))
        raise
    print("Finished initialization")


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
    if not isinstance(time, datetime):
        raise TypeError('Expected datetime, got ' + type(time).__name__ + '.')
    content = {}
    content['last_run'] = time.isoformat()
    with open("lastrun.json", "w") as fh:
        json.dump(content, fh)


def get_completed_items_since(time):
    """Return list of completed tasks since given timestamp."""
    if not isinstance(time, datetime):
        raise TypeError('Expected datetime, got ' + type(time).__name__ + '.')
    completed = __todoist.completed.get_all(
            since=time.strftime("%Y-%m-%dT%H:%M"))
    print("Found "
          + str(len(completed["items"]))
          + " completed tasks since "
          + str(time))
    tasks = []
    for task in completed["items"]:
        tasks.append(__todoist.items.get_by_id(task["task_id"]))
    return tasks


def matches(task, config):
    """Check if a task matches a configured filter."""
    if "labels" in config["filter"].keys():
        for label in config["filter"]["labels"]:
            if label["id"] not in task["labels"]:
                return False
    if "project" in config["filter"].keys():
        if config["filter"]["project"]["id"] != task["project_id"]:
            return False
    return True


def make_filter(config):
    """Return filter function for finding tasks matching the config."""
    def filt(task):
        return matches(task, config)

    return filt


def recreate_completed_tasks():
    """Recreate task that were completed since last run."""
    last_run = read_time_of_last_run()
    current_time = datetime.utcnow()
    completed = get_completed_items_since(last_run)
    for completed_task in completed:
        recreate_task = False
        skip_label = None
        for tasktype in __config["tasks"]:
            if not tasktype["recreate_when_completed"]:
                continue
            if matches(completed_task, tasktype):
                recreate_task = True
                if "skip_label_on_recreate" in tasktype.keys():
                    skip_label = tasktype["skip_label_on_recreate"]
                break
        if recreate_task:
            print("Recreating task '" + completed_task["content"] + "'")
            labels = completed_task["labels"]
            if skip_label["id"] in labels:
                labels.remove(skip_label["id"])
                print("Skipping label '" + skip_label["name"] + "'")
            new_task = __todoist.items.add(
                    completed_task["content"],
                    project_id=completed_task["project_id"],
                    section_id=completed_task["section_id"],
                    labels=labels)
            print(new_task)
            if not __dry:
                __todoist.commit()
    if not __dry:
        write_time_of_last_run(current_time)


def update_tasks():
    """Update tasks if a trigger matches."""
    # TODO Loop over all uncompleted tasks and check if any trigger matches
    # If trigger matches and properties are not updated yet, update task
    for tasktype in __config["tasks"]:
        filt = make_filter(tasktype)
        tasks = __todoist.items.all(filt)
        for task in tasks:
            for action in tasktype["actions"]:
                pass


def main():
    """Recurrist's main function."""
    try:
        init()
        recreate_completed_tasks()
        update_tasks()
    except Exception:
        return 1


if __name__ == '__main__':
    sys.exit(main())
