from config_reader import Config
from gitlab_api import GitlabApi
from jira_api import JiraApi, JiraIssue
import os
from synchronizer import Synchronizer

if __name__ == "__main__":
    jira_base_url = os.environ["JIRA_URL"]
    issue_key = "PLAT-2"
    jira_token = os.environ["JIRA_TOKEN"]

    jira = JiraApi(jira_base_url, jira_token)

    gitlab_base_url = os.environ["GITLAB_BASE_URL"]
    gitlab_access_token = os.environ["GITLAB_TOKEN"]

    print("Read base URL: " + gitlab_base_url)
    print("Read access token: (length: " + str(len(gitlab_access_token)) + ")")

    gitlab_api = GitlabApi(base_url=gitlab_base_url, access_token=gitlab_access_token)

    config = Config("config.json")

    print("Synchronizing Gitlab => JIRA")
    sync = Synchronizer(jira_api=jira, gitlab_api=gitlab_api, gitlab_group="galileo-genai", gitlab_project="aws-infra",
                        config=config)
    sync.sync_gitlab_to_jira()

