from typing import Any, Dict, List, Optional
import requests
import base64
import json


class GitHubAPI:
    """
    A class to interact with the GitHub API.
    """

    def __init__(self, github_token: str, repo_name: str):
        """
        Initializes the GitHubAPI class.

        Args:
            github_token (str): GitHub personal access token with repo scope.
            repo_name (str): GitHub repository name in the format "{owner}/{repo}".
        """
        self.github_token = github_token
        self.repo_name = repo_name
        self.headers = {"Authorization": f"token {self.github_token}"}
        self.api_base_url = f"https://api.github.com/repos/{self.repo_name}"

    def _get_file_data(
        self, path: str, required: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the data of a file from the GitHub repository.

        Args:
            path (str): Path to the file in the repository.
            required (bool, optional): Whether the file is required. Defaults to False.

        Returns:
            Optional[Dict[str, Any]]: Data of the file if it exists, otherwise None.
        """
        url = f"{self.api_base_url}/contents/{path}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                if required:
                    print(f"File not found: {path}")
                return None
            else:
                print(
                    f"HTTP error occurred while fetching file data for {path}: {http_err}"
                )
                raise
        except Exception as e:
            print(f"Failed to get file data for {path}: {e}")
            raise

    def _get_file_content(self, path: str, decoded: bool = True, required: bool = True) -> Optional[str]:
        """
        Retrieve the content of a file from the GitHub repository.

        Args:
            path (str): Path to the file in the repository.
            decoded (bool, optional): Whether to decode the content. Defaults to True.
            required (bool, optional): Whether the file is required. Defaults to True.

        Returns:
            Optional[str]: Content of the file if it exists, otherwise None.
        """
        try:
            content = self._get_file_data(path, required=required)
            if not content:
                if required:
                    print(f"Failed to get file content for {path}")
                return None
            elif not "content" in content or len(content["content"]) == 0:
                file_content = requests.get(content["download_url"]).content
            else:
                file_content = base64.b64decode(content["content"])
            if decoded:
                return file_content.decode()
            else:
                return file_content

        except Exception as e:
            print(f"Failed to get file content for {path}: {e}")
            raise

    def _get_directory_contents(self, dir_path: str) -> List[Dict[str, Any]]:
        """
        Retrieve the contents of a directory from the GitHub repository.

        Args:
            dir_path (str): Path to the directory in the repository.

        Returns:
            List[Dict[str, Any]]: List of metadata for each item in the directory.
        """
        url = f"{self.api_base_url}/contents/{dir_path}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            contents = response.json()
            if not type(contents) == list:
                raise Exception(f"Invalid directory contents: {contents}")
            return contents

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                print(f"Directory not found: {dir_path}")
                return []
            else:
                print(
                    f"HTTP error occurred while fetching directory contents for {dir_path}: {http_err}"
                )
                raise
        except Exception as e:
            print(
                f"Error occurred while fetching directory contents for {dir_path}: {e}"
            )
            raise

    def _create_file(
        self, path: str, message: str, content: Any, is_binary: bool = False
    ) -> None:
        """
        Create a new file in the GitHub repository.

        Args:
            path (str): Path to the file in the repository.
            message (str): Commit message.
            content (Any): Content of the file.
            is_binary (bool, optional): Whether the content is binary data. Defaults to False.
        """
        url = f"{self.api_base_url}/contents/{path}"
        if is_binary:
            content = base64.b64encode(content).decode()
        else:
            content = base64.b64encode(content.encode()).decode()
        data = {"message": message, "content": content}
        try:
            existing_file = self._get_file_data(path, required=False)
            if existing_file:
                print(f"File already exists: {path}")
                return
            response = requests.put(url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            print(f"File created successfully: {path}")

        except Exception as e:
            print(f"Failed to create file {path}: {e}")
            raise

    def _update_file(
        self, path: str, message: str, content: Any, is_binary: bool = False
    ) -> None:
        """
        Update an existing file in the GitHub repository.

        Args:
            path (str): Path to the file in the repository.
            message (str): Commit message.
            content (Any): Content of the file.
            is_binary (bool, optional): Whether the content is binary data. Defaults to False.
        """
        url = f"{self.api_base_url}/contents/{path}"
        try:
            existing_file = self._get_file_data(path, required=True)
            if not existing_file:
                print(f"Failed to update file: {path}")
                return
            if is_binary:
                content = base64.b64encode(content).decode()
            else:
                content = base64.b64encode(content.encode()).decode()
            data = {"message": message, "content": content, "sha": existing_file["sha"]}
            response = requests.put(url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            print(f"File updated successfully: {path}")

        except Exception as e:
            print(f"Failed to update file {path}: {e}")
            raise

    def _delete_file(self, path: str, message: str, required: bool = True) -> None:
        """
        Delete a file from the GitHub repository.

        Args:
            path (str): Path to the file in the repository.
            message (str): Commit message.
            required (bool, optional): Whether the file is required. Defaults to True.
        """
        url = f"{self.api_base_url}/contents/{path}"
        data = {"message": message}
        try:
            existing_file = self._get_file_data(path, required=required)
            if not existing_file:
                if required:
                    print(f"Failed to delete file: {path}")
                return
            data["sha"] = existing_file["sha"]
            response = requests.delete(url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            print(f"File deleted successfully: {path}")

        except Exception as e:
            print(f"Failed to delete file {path}: {e}")
            raise

    def _move_file(self, old_path: str, new_path: str) -> None:
        """
        Move a file from one location to another in the GitHub repository.

        Args:
            old_path (str): Old path to the file.
            new_path (str): New path to the file.
        """
        try:
            content = self._get_file_data(old_path, required=True)
            if not content:
                print(f"Failed to move file: {old_path} -> {new_path}")
                return
            elif not "content" in content or len(content["content"]) == 0:
                file_data = requests.get(content["download_url"]).content
            else:
                file_data = base64.b64decode(content["content"])
            self._create_file(
                new_path,
                f"Move file: {content['name']} from {old_path} to {new_path}",
                file_data,
                is_binary=True,
            )
            self._delete_file(
                old_path,
                f"Move file: {content['name']} from {old_path} to {new_path}",
            )
            print(f"File moved successfully: {old_path} -> {new_path}")

        except Exception as e:
            print(f"Failed to move file: {old_path} -> {new_path}: {e}")


if __name__ == "__main__":
    """
    For testing
    """
    import os

    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    config = json.load(open("../secrets/config.json"))
    github_token = config["github_token"]
    repo = config["repo"]
    api = GitHubAPI(github_token, repo)
    print(api._get_directory_contents(""))
    api._create_file("test.txt", "Create test file", "Hello, World!")
    api._update_file("test.txt", "Update test file", "Hello, GitHub!")
    api._move_file("test.txt", "test/test.txt")
    api._delete_file("test/test.txt", "Delete test file")
    print(api._get_directory_contents(""))
