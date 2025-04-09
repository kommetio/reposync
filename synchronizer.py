from jira_api import JiraApi
from gitlab_api import GitlabApi
from issue_mapping import IssueMapper
from config_reader import Config


class Synchronizer:

    def __init__(self, jira_api: JiraApi, gitlab_api: GitlabApi, gitlab_group, gitlab_project, config: Config):
        self.jira_api = jira_api
        self.gitlab_api = gitlab_api
        self.gitlab_group = gitlab_group
        self.gitlab_project = gitlab_project
        self.mapper = IssueMapper()
        self.config = config

    def is_synchronizable(self, item, issue_type):

        labels = item["labels"]
        filters = self.config.get_filters()
        required_labels = []

        for f in filters:
            if f["issue_type"] == issue_type and f["label"] is not None:
                required_labels.append(f["label"])

        if len(required_labels) == 0:
            return True

        for rl in required_labels:
            is_found = False
            for actual_label in labels:
                if actual_label == rl:
                    is_found = True
                    break
            if not is_found:
                # required label not found
                return False

        return True

    def sync_epics(self):

        gitlab_epics = self.gitlab_api.get_epics(group_id=self.gitlab_group)
        print("Retrieved Gitlab epics: " + str(len(gitlab_epics)))

        epics_created = 0
        max_epics_created = 1

        for ge in gitlab_epics:

            if not self.is_synchronizable(ge, "epic"):
                print("Epic not synchronizable: " + ge["title"])
                continue

            gitlab_epic_id = ge["id"]

            # check if the epic exists in the mapping file
            jira_epic_id = self.mapper.get_jira_issue(gitlab_issue=gitlab_epic_id, type="epic")

            if jira_epic_id is None:

                # epic does not exist in JIRA, create it
                if epics_created < max_epics_created:
                    jira_epic_id = self.jira_api.create_issue(project_key=self.config.jira_project_key,
                                                              issue_type="Epic", title=ge["title"],
                                                              description=ge["description"])

                    # create a mapping between the JIRA and Gitlab issues
                    self.mapper.store_mapping(jira_issue=jira_epic_id, gitlab_issue=gitlab_epic_id, type="epic")

                    epics_created = epics_created + 1

            else:

                # update existing epic
                self.jira_api.create_issue(project_key=self.config.jira_project_key,
                                           issue_type="Epic", title=ge["title"],
                                           description=ge["description"], issue_id=jira_epic_id)

        return None

    def sync_issues(self):

        max_issues = 1000

        # get all issues from gitlab
        gitlab_issues = self.gitlab_api.get_issues(group_name=self.gitlab_group, project_name=self.gitlab_project,
                                                   issue_count=max_issues)

        print("Retrieved Gitlab issues: " + str(len(gitlab_issues)))

        max_issues_created = 1
        issues_created = 0

        for gi in gitlab_issues:

            if not self.is_synchronizable(gi, "non-epic"):
                print("Issue not synchronizable: " + gi["title"])
                continue

            gitlab_issue_id = str(gi["id"])

            # check if the issue exists in the mapping file
            jira_issue_id = self.mapper.get_jira_issue(gitlab_issue=gi["id"], type="issue")

            jira_issue_type = self._get_issue_type(gi)

            if not jira_issue_type:
                raise "Issue type not determined based on rules"

            if jira_issue_id is None:

                if issues_created < max_issues_created:
                    # create a JIRA issue for the Gitlab issue
                    jira_issue_id = self.jira_api.create_issue(project_key=self.config.jira_project_key,
                                                               issue_type=jira_issue_type, title=gi["title"],
                                                               description=gi["description"])

                    # create a mapping between the JIRA and Gitlab issues
                    self.mapper.store_mapping(jira_issue=jira_issue_id, gitlab_issue=gitlab_issue_id, type="issue")

                    issues_created = issues_created + 1
                else:
                    print("Not creating issue (max = " + str(max_issues_created) + ")")

            else:
                print("Found mapping: GITLAB[" + gitlab_issue_id + "] => JIRA[" + jira_issue_id + "]")

            # update JIRA status based on rules
            jira_issue_status = self._get_issue_status(gi)

            if jira_issue_status is not None:
                print("Updating status to")

    def sync_gitlab_to_jira(self):
        self.sync_epics()
        #self.sync_issues()
        return None

    def _get_issue_type(self, gi):

        labels = gi["labels"]
        issue_type = None

        if not labels:
            raise "Gitlab issue labels not returned from API"

        for gitlab_label in labels:

            for rule in self.config.rules:
                if rule["type"] == "label_to_issue_type":
                    if rule["label"] == gitlab_label:
                        if issue_type is None:
                            issue_type = rule["issue_type"]
                        else:
                            raise "Duplicate issue type mapping for label " + gitlab_label

        return issue_type

    def _get_issue_status(self, gi):

        labels = gi["labels"]
        status = None

        if not labels:
            raise "Gitlab issue labels not returned from API"

        for gitlab_label in labels:

            for rule in self.config.rules:
                if rule["type"] == "label_to_status":
                    if rule["label"] == gitlab_label:
                        if status is None:
                            status = rule["status"]
                        else:
                            raise "Duplicate issue status mapping for label " + gitlab_label

        return status
