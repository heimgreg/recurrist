from datetime import datetime
from todoist.api import TodoistAPI


class TodoistWrapper:
    def __init__(self, token):
        self.token = token
        self.api = TodoistAPI(token)
        try:
            syncres = self.api.sync()
            if 'error' in syncres:
                raise Exception(syncres["error"])
            print("Successfully synced with Todoist")
        except Exception as e:
            print("Failed to sync with todoist: " + str(e))
            raise

    def find_label_by_name(self, name):
        labels = self.api.labels.all()
        for label in labels:
            if label['name'] == name:
                return label
        return None

    def get_completed_items_since(self, time):
        if type(time) != datetime:
            raise TypeError('Expected datetime, got '
                            + type(time).__name__ + '.')
        completed = self.api.completed.get_all()
        completed["items"] = [x for x in completed["items"]
                              if datetime.fromisoformat(
                                  x["completed_date"][:-1] + '+00:00') > time]
        return completed["items"]

    def get_task_details(self, task_id):
        return self.api.items.get_by_id(task_id)

    def get_label_details(self, label_id):
        return self.api.labels.get_by_id(label_id)
