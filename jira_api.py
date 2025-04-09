import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraIssue:

    def __init__(self, issue_key, status, summary):
        self.issue_key = issue_key
        self.status = status
        self.summary = summary


class JiraApi:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

    def get_issue(self, issue_key) -> JiraIssue:
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            if response.status_code == 200:
                issue_data = response.json()
                return JiraIssue(issue_key=issue_key, status=issue_data['fields']['status']['name'],
                                 summary=issue_data['fields']['summary'])
            else:
                print("Failed to fetch issue")
                print("Status Code:", response.status_code)
                print("Response:", response.text)
        except requests.RequestException as e:
            print("Request failed:", e)

    def get_issues(self, project_key) -> list[JiraIssue]:
        jql = f"project={project_key}"
        url = f"{self.base_url}/rest/api/2/search"
        params = {
            "jql": jql,
            "fields": "summary,status",
            "maxResults": 100
        }

        issues = []
        try:
            response = requests.get(url, headers=self.headers, params=params, verify=False)
            if response.status_code == 200:
                data = response.json()
                for issue in data.get("issues", []):
                    issues.append(
                        JiraIssue(
                            issue_key=issue["key"],
                            status=issue["fields"]["status"]["name"],
                            summary=issue["fields"]["summary"]
                        )
                    )
            else:
                print("Failed to fetch issues")
                print("Status Code:", response.status_code)
                print("Response:", response.text)
        except requests.RequestException as e:
            print("Request failed:", e)

        return issues

    def create_issue(self, title, issue_type, description, project_key, issue_id=None):

        is_update = issue_id is not None

        url = (
            f"{self.base_url}/rest/api/2/issue/{issue_id}" if is_update
            else f"{self.base_url}/rest/api/2/issue"
        )

        payload = {
            "fields": {
                "summary": title,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }

        if not is_update:
            payload["fields"]["project"] = {"key": project_key}

        if issue_type == "Epic":
            payload["fields"]["customfield_10104"] = title

            # inm Gitlab, epic description is optional, but in JIRA it's required
            if payload["fields"]["description"] is None or len(payload["fields"]["description"]) == 0:
                payload["fields"]["description"] = "<empty>"

        try:
            if is_update:
                response = requests.put(url, json=payload, headers=self.headers, verify=False)
            else:
                response = requests.post(url, json=payload, headers=self.headers, verify=False)

            if response.status_code in [200, 201, 204]:
                if is_update:
                    print(f"Issue {issue_id} updated successfully.")
                    return issue_id
                else:
                    issue_data = response.json()
                    jira_issue_key = issue_data['key']
                    print(f"Issue {jira_issue_key} created successfully.")
                    return jira_issue_key
            else:
                action = "update" if is_update else "create"
                print(f"Failed to {action} issue")
                print("Status Code:", response.status_code)
                print("Response:", response.text)
        except requests.RequestException as e:
            print("Request failed:", e)

    def update_issue_status(self, issue_key: str, new_status_name: str):
        # Step 1: Get available transitions
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            if response.status_code != 200:
                raise Exception(f"Issue '{issue_key}' not found or failed to get transitions. Status code: {response.status_code}")
        except requests.RequestException as e:
            raise Exception(f"Failed to get transitions for issue '{issue_key}': {e}")

        transitions = response.json().get("transitions", [])
        matching_transition = next((t for t in transitions if t["to"]["name"].lower() == new_status_name.lower()), None)

        if not matching_transition:
            raise Exception(f"No matching transition found for status '{new_status_name}' in issue '{issue_key}'.")

        transition_id = matching_transition["id"]

        # Step 2: Perform the transition
        transition_url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
        payload = {
            "transition": {
                "id": transition_id
            }
        }

        try:
            update_response = requests.post(transition_url, headers=self.headers, json=payload, verify=False)
            if update_response.status_code == 204:
                print(f"Issue '{issue_key}' successfully transitioned to '{new_status_name}'.")
            else:
                raise Exception(f"Failed to transition issue '{issue_key}'. Status code: {update_response.status_code}, Response: {update_response.text}")
        except requests.RequestException as e:
            raise Exception(f"Failed to update status for issue '{issue_key}': {e}")

