import json


class Config:

    def __init__(self, filepath):
        self.filepath = filepath
        self.rules = []
        self.jira_project_key = None
        self.filters = []
        self._load_rules()

    def _load_rules(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.rules = data.get("gitlab_to_jira", {}).get("rules", [])
                self.filters = data.get("gitlab_to_jira", {}).get("filters", [])
                self.jira_project_key = data.get("gitlab_to_jira", {}).get("jira_project_key")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading rules from {self.filepath}: {e}")
            self.rules = []

    def get_rules(self):
        return self.rules

    def get_filters(self):
        return self.filters
