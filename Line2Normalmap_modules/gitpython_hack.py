import io
from typing import Tuple

import pygit2


class Git:
    """
    Git wrapper class.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_object_header(self, ref: str) -> Tuple[str, str, int]:
        repo = pygit2.Repository(self.repo_path)
        obj = repo.revparse_single(ref)
        return obj.hex, obj.type, obj.size

    def stream_object_data(self, ref: str) -> Tuple[str, str, int, io.BytesIO]:
        repo = pygit2.Repository(self.repo_path)
        obj = repo.revparse_single(ref)
        data = obj.data
        bio = io.BytesIO(data)
        return obj.hex, obj.type, obj.size, bio


class Repo:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.git = Git(repo_path)
