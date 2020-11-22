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
        except Exception as e:
            print("Failed to sync with todoist: " + str(e))
            raise
