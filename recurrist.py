#!/usr/bin/env python3

"""Automation for Todoist.

With this module, tasks in Todoist can be
* recreated after completion for recurring tasks without due dates,
* updated automatically.
"""

import sys
import json
import logging
from os import environ
from datetime import datetime, date, timedelta
from dateutil import parser
from todoist.api import TodoistAPI
from jsonschema import validate, ValidationError, SchemaError


__config = {}
__logger = None
__todoist = None
__dry = False


def load_config(filename="config.json"):
    """Load configuration from config file config.json."""
    global __config
    schema = None
    with open("config.schema", "r") as schemafile:
        schema = json.load(schemafile)
    __logger.debug("Loading configuration file " + filename)
    with open(filename, "r") as config_file:
        __config = json.load(config_file)
    try:
        validate(schema=schema, instance=__config)
    except ValidationError as e:
        __logger.error("Invalid configuration format: " + e.message)
        raise Exception("Failed to validate configuration schema")
    except SchemaError as e:
        __logger.error("Invalid schema file: " + e.message)
        raise Exception("Failed to validate configuration schema")
    __logger.debug("Successfully checked format of configuration file.")


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
        if "actions" in task.keys():
            for action in task["actions"]:
                if "add_label" in action["action"].keys():
                    label = find_label_by_name(action["action"]["add_label"])
                    if label is None:
                        unknown_label(action["action"]["add_label"])
                    action["action"]["add_label"] = label
                if "move_to_project" in action["action"].keys():
                    proj = find_project_by_name(
                            action["action"]["move_to_project"])
                    if proj is None:
                        unknown_project(action["action"]["move_to_project"])
                    action["action"]["move_to_project"] = proj
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


def parse_todoist_datetime(timestring):
    """Parse datetime string from to todoist's format to datetime object."""
    dt = parser.isoparse(timestring)
    return dt


def get_todoist_token():
    """Load Todoist API token from environment variable TODOIST_TOKEN."""
    token = environ.get('TODOIST_TOKEN')
    if token is None:
        raise Exception('Environment variable TODOIST_TOKEN not set!')
    return token


def connect(token):
    """Connect to Todoist API."""
    global __todoist
    __logger.info("Connecting to Todoist API")
    __todoist = TodoistAPI(token)
    try:
        syncres = __todoist.sync()
        if 'error' in syncres:
            raise Exception(syncres["error"])
        __logger.debug("Successfully synced with Todoist")
    except Exception as e:
        __logger.error(str(e))
        raise Exception("Unable to connect to Todoist")


def init_logger():
    """Initialize log settings."""
    global __logger
    __logger = logging.getLogger("recurrist_log")
    __logger.setLevel(logging.DEBUG)
    chformatter = logging.Formatter(
            '%(levelname)-8s %(module)s : %(message)s')
    fhformatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(module)s : %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(chformatter)
    fh = logging.FileHandler("recurrist.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fhformatter)
    __logger.addHandler(ch)
    __logger.addHandler(fh)


def init():
    """Initialize Recurrist."""
    __logger.debug("Starting initialization")
    try:
        load_config()
        token = get_todoist_token()
        connect(token)
        replace_names_in_config()
    except Exception as e:
        __logger.error(str(e))
        raise Exception("Error while initializing Recurrist")
    __logger.debug("Finished initialization")


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
    __logger.debug("Found "
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


def make_filter(config, uncompleted=True):
    """Return filter function for finding tasks matching the config."""
    def filt(task):
        if uncompleted:
            return (matches(task, config) and task["checked"] == 0)
        return matches(task, config)

    return filt


def triggers(task, trigger):
    """Check if task matches trigger conditions."""
    if "days_since_creation" in trigger.keys():
        creation = parse_todoist_datetime(task["date_added"])
        trigger_date = creation.date() + timedelta(
                days=trigger["days_since_creation"])
        if date.today() >= trigger_date:
            return True
    if "days_until_due" in trigger.keys():
        if task["due"] is not None:
            due = parse_todoist_datetime(task["due"]["date"])
            trigger_date = due.date() - timedelta(
                    days=trigger["days_until_due"])
            if date.today() >= trigger_date:
                return True
    return False


def commit():
    """Commit changes."""
    try:
        commitres = __todoist.commit()
        if 'error' in commitres:
            raise Exception(commitres["error"])
        __logger.debug("Committed successfully")
    except Exception as e:
        __logger.error(str(e))
        raise Exception("Failed to commit")


def recreate_completed_tasks():
    """Recreate task that were completed since last run."""
    last_run = read_time_of_last_run()
    current_time = datetime.utcnow()
    if last_run is None:
        __logger.warning(
                "Could not load time of last run. Using current time.")
        last_run = current_time
    completed = get_completed_items_since(last_run)
    num_recreated = 0
    for completed_task in completed:
        recreate_task = False
        skip_label = None
        prio = completed_task["priority"]
        for tasktype in __config["tasks"]:
            if not tasktype["recreate_when_completed"]:
                continue
            if matches(completed_task, tasktype):
                recreate_task = True
                if "skip_label_on_recreate" in tasktype.keys():
                    skip_label = tasktype["skip_label_on_recreate"]
                if "set_priority_on_recreate" in tasktype.keys():
                    prio = 5 - tasktype["set_priority_on_recreate"]
                break
        if recreate_task:
            __logger.debug("Recreating task '"
                           + completed_task["content"] + "'")
            labels = completed_task["labels"]
            if skip_label is not None and skip_label["id"] in labels:
                labels.remove(skip_label["id"])
                __logger.debug("Skipping label '" + skip_label["name"] + "'")
            __todoist.items.add(
                    completed_task["content"],
                    project_id=completed_task["project_id"],
                    section_id=completed_task["section_id"],
                    priority=prio,
                    labels=labels)
            num_recreated += 1
    if not __dry:
        if num_recreated > 0:
            try:
                commit()
            except Exception as e:
                __logger.error(str(e))
                raise Exception("Error while recreating completed tasks")
        write_time_of_last_run(current_time)
    __logger.info("Recreated " + str(num_recreated) + " tasks")


def perform_action(task, action):
    """Update task according to defined action."""
    updated = False
    if "add_label" in action.keys():
        labels = task["labels"]
        if action["add_label"]["id"] not in labels:
            labels.append(action["add_label"]["id"])
            __logger.debug("Updating task '"
                           + task["content"]
                           + "': Adding label '"
                           + action["add_label"]["name"]
                           + "'.")
            task.update(labels=labels)
            updated = True
        else:
            __logger.debug("Task '"
                           + task["content"]
                           + "' already has label '"
                           + action["add_label"]["name"]
                           + "'.")
    if "increase_priority" in action.keys():
        current_prio = task["priority"]
        # p1 has value 4 in Todoist API
        new_prio = 5 - action["increase_priority"]
        if current_prio < new_prio:
            __logger.debug("Updating task '"
                           + task["content"]
                           + "': Increasing priority from p"
                           + str(5 - current_prio)
                           + " to p" + str(5 - new_prio) + ".")
            task.update(priority=new_prio)
            updated = True
        else:
            __logger.debug("Task '"
                           + task["content"]
                           + "' already has priority p"
                           + str(5 - new_prio) + ".")
    if "move_to_project" in action.keys():
        current_proj = task["project_id"]
        if current_proj != action["move_to_project"]["id"]:
            print("vor log")
            __logger.debug("Updating task '"
                           + task["content"]
                           + "': Moving to project '"
                           + action["move_to_project"]["name"]
                           + "'.")
            task.update(project_id=action["move_to_project"]["id"])
            updated = True
        else:
            __logger.debug("Task '"
                           + task["content"]
                           + "' already in project '"
                           + action["move_to_project"]["name"]
                           + "'.")
    return updated


def update_tasks():
    """Update tasks if a trigger matches."""
    num_updated = 0
    for tasktype in __config["tasks"]:
        filt = make_filter(tasktype)
        tasks = __todoist.items.all(filt)
        for task in tasks:
            updated = False
            if "actions" in tasktype.keys():
                for action in tasktype["actions"]:
                    if triggers(task, action["trigger"]):
                        if perform_action(task, action["action"]):
                            updated = True
            if updated:
                num_updated += 1
    if not __dry and num_updated > 0:
        try:
            commit()
        except Exception as e:
            __logger.error(str(e))
            raise Exception("Error while recreating completed tasks")
    __logger.info("Updated " + str(num_updated) + " tasks")


def main():
    """Recurrist's main function."""
    init_logger()
    try:
        init()
    except Exception as e:
        __logger.error(str(e))
        return 1
    if __dry:
        __logger.warning("Dry run! No changes will be performed.")
    try:
        recreate_completed_tasks()
    except Exception as e:
        __logger.error(str(e))
    try:
        update_tasks()
    except Exception as e:
        __logger.error(str(e))
    return 0


if __name__ == '__main__':
    sys.exit(main())
