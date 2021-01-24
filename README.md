# Recurrist

Recurring Tasks in Todoist without due dates.

This tool was created to follow the idea to only assign due dates to tasks with a real deadline.
Most regular task don't need to be done on certain days so Todoist's recurring tasks feature contradicts this idea.

Still having regular tasks is achieved by recreating completed tasks and updating them regularly to increase their priority and adding the *next* label.
This way, tasks climb up the next actions list until they are the top task.

A Todoist Premium account is required to use Recurrist as it needs access to the list of completed tasks.

Recurrist is not created by, affiliated with, or supported by Doist.

## Features

* Recreate tasks when completed
* Change properties when recreating a completed task
* Trigger task updates relative to creation date
* Trigger task updates relative to due date

## How it works

The script is meant to run regularly, at least once a day.
On each run, it checks for completed tasks since the last run which need to be recreated.

The tasks matching the defined properties are then updated to increase priority.

You will need to have python3 and the requirements (see requirements.txt) installed.
Call `./recurrist.json config.json` with you settings saved in `config.json`, see below for details.

## Configuration

Task filters and update triggers are configured in a json file. A schema for the file format is defined in config.schema.

The format can be summarized as follows:

* `tasks` contains a list of task types
* Each task type has a filter to identify tasks of that type (e.g., a label) and a list of actions
* Each item in the list of actions then consists of a trigger (e.g., days since creation) and the actual action (e.g., increase priority)

### Example Config

This example defines tasks that shall recur weekly. The relevant tasks are identified by the label *recurWeekly*.

4 days after task creation, the *next* label is added so the task will appear on the next actions list.
On days 5, 6, and 7 the priority is increased to p3, p2, and p1, respectively.
Hence, after one week, the task appears on the next actions list with highest priority.
After completion it is automatically recreated with priority p4 and without the *next* label.

```json
{
  "tasks": [
    {
      "filter": {
        "labels": [
          "recurWeekly"
        ]
      },
      "actions": [
        {
          "trigger": {
            "days_since_creation": 4
          },
          "action": {
            "add_label": "next"
          }
        },
        {
          "trigger": {
            "days_since_creation": 5
          },
          "action": {
            "increase_priority": 3
          }
        },
        {
          "trigger": {
            "days_since_creation": 6
          },
          "action": {
            "increase_priority": 2
          }
        },
        {
          "trigger": {
            "days_since_creation": 7
          },
          "action": {
            "increase_priority": 1
          }
        }
      ],
      "recreate_when_completed": true,
      "skip_label_on_recreate": "next",
      "set_priority_on_recreate": 4
    }
  ]
}
```
