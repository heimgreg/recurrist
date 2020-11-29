import sys
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
