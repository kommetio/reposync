import csv
import os


class IssueMapper:
    def __init__(self, csv_path="issue_mapping.csv"):
        self.csv_path = csv_path
        # create the file if it does not exist
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode='w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["jira_issue", "gitlab_issue", "type"])
                writer.writeheader()

    def store_mapping(self, jira_issue, gitlab_issue, type):
        # check for duplicates
        if not self.get_jira_issue(gitlab_issue, type):
            with open(self.csv_path, mode='a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["jira_issue", "gitlab_issue", "type"])
                writer.writerow({
                    "jira_issue": jira_issue,
                    "gitlab_issue": gitlab_issue,
                    "type": type
                })

    def get_jira_issue(self, gitlab_issue, type):
        with open(self.csv_path, mode='r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row["gitlab_issue"]) == str(gitlab_issue) and row["type"] == type:
                    return str(row["jira_issue"])
        return None
