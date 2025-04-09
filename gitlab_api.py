import requests


class GitlabApi:
    def __init__(self, base_url, access_token):
        self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def list_projects(self):
        """
        Returns a list of available projects for the authenticated user.
        :return: List of dictionaries containing project details
        """
        url = f"{self.base_url}/api/v4/projects"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            projects = response.json()
            return [project['name'] for project in projects]
        else:
            raise Exception(f"Failed to fetch projects: {response.status_code} - {response.text}")

    def list_group_projects(self, group_id):
        """
        Returns a list of project names under a specific group
        :param group_id: ID or URL-encoded path of the group
        :return: array of strings denoting project names
        """
        url = f"{self.base_url}/api/v4/groups/{group_id}/projects"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return [project["name"] for project in response.json()]
        else:
            raise Exception(f"Failed to fetch group projects: {response.status_code} {response.text}")

    def get_commits(self, group_name, project_name, commit_count=20):
        """
        Retrieves all commits for a given project
        :param project_name: project name
        :param group_name: group name
        :param commit_count: the number of commits to be returned; defaults to 20
        :return: JSON list of commit objects
        """

        project_id = self.get_project_id(group_name, project_name)

        url = f"{self.base_url}/api/v4/projects/{project_id}/repository/commits?per_page=" + str(commit_count)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_issues(self, group_name, project_name, issue_count=20):

        project_id = self.get_project_id(group_name, project_name)

        url = f"{self.base_url}/api/v4/projects/{project_id}/issues?per_page=" + str(issue_count)
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_project_id(self, group_id, project_name):
        """
        Retrieves the project ID based on its name and group
        :param group_id: ID of the group
        :param project_name: Name of the project
        :return: Project ID if found, None otherwise
        """
        url = f"{self.base_url}/api/v4/groups/{group_id}/projects?per_page=100"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            projects = response.json()
            for project in projects:
                if project["name"].lower() == project_name.lower():
                    return project["id"]
        return None

    def search_comments(self, group_name, project_name, comment_count=20, keyword=None):
        """
        Retrieves the latest comments from a project, with an optional keyword filter
        :param comment_count: number of comments to return
        :param group_name: name of the group
        :param project_name: the name of the project
        :param keyword: Optional keyword to filter comments
        :return: JSON list of comment objects
        """
        project_id = self.get_project_id(group_name, project_name)
        url = f"{self.base_url}/api/v4/projects/{project_id}/issues_notes?per_page=" + str(comment_count)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            comments = response.json()
            if keyword:
                comments = [comment for comment in comments if keyword.lower() in comment['body'].lower()]
            return comments
        return []

    def search_issues(self, group_name, project_name, keyword, search_in='title,description'):
        """
        Searches for issues in a specific project that contain the given keyword.

        :param group_name: ID of the project.
        :param project_name: ID of the project.
        :param keyword: The keyword to search for.
        :param search_in: Comma-separated fields to search in. Defaults to 'title,description'.
                          Other options include 'title' or 'description'.
        :return: JSON list of matching issue objects.
        """
        project_id = self.get_project_id(group_name, project_name)
        url = f"{self.base_url}/api/v4/projects/{project_id}/issues"
        params = {
            'search': keyword,
            'in': search_in,
            'per_page': 1000  # Adjust as needed; be mindful of performance and API limits
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_epics(self, group_id):
        """
        Retrieves all epics from a specific GitLab group.

        :param group_id: The ID or URL-encoded path of the group.
        :return: A list of epic dictionaries.
        """
        url = f"{self.base_url}/api/v4/groups/{group_id}/epics"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch epics: {response.status_code} - {response.text}")

