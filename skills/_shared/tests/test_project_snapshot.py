"""project_snapshot: items of another repository must never be keyed or counted."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from project_snapshot import read_snapshot  # noqa: E402

KEY_MAP = {"E01": {"number": 1}, "E01-I01": {"number": 2}}


def node(repo, number, title):
    return {"id": f"PVTI_{repo}_{number}", "fieldValues": {"nodes": []},
            "content": {"id": f"I_{number}", "number": number, "title": title, "state": "OPEN", "closedAt": None,
                        "repository": {"nameWithOwner": repo}, "parent": None, "labels": {"nodes": []}}}


class StubRunner:
    def __init__(self, nodes):
        self.nodes = nodes

    def graphql(self, query, variables, write=False):
        assert not write
        return {"repositoryOwner": {"projectV2": {"id": "PVT_x", "title": "sample", "items": {
            "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": self.nodes}}}}


MIXED = [node("example-org/sample-repo", 1, "epic"), node("other-org/other-repo", 1, "foreign #1"),
         node("example-org/sample-repo", 2, "story")]


class ProjectSnapshotRepoFilterTest(unittest.TestCase):
    def test_other_repo_issue_1_is_excluded_not_keyed_e01(self):
        snap = read_snapshot(StubRunner(MIXED), "example-org", 9, KEY_MAP, "Example-Org/Sample-Repo")
        self.assertEqual([(i["repo"], i["number"], i["key"]) for i in snap["items"]],
                         [("example-org/sample-repo", 1, "E01"), ("example-org/sample-repo", 2, "E01-I01")])
        self.assertEqual(snap["excludedOtherRepo"], 1)
        self.assertEqual(snap["repo"], "Example-Org/Sample-Repo")

    def test_multi_repo_project_without_repo_is_refused(self):
        with self.assertRaises(ValueError) as cm:
            read_snapshot(StubRunner(MIXED), "example-org", 9, KEY_MAP, None)
        self.assertIn("--repo", str(cm.exception))

    def test_single_repo_project_without_repo_keeps_number_lookup(self):
        snap = read_snapshot(StubRunner(MIXED[:1] + MIXED[2:]), "example-org", 9, KEY_MAP, None)
        self.assertEqual([i["key"] for i in snap["items"]], ["E01", "E01-I01"])


if __name__ == "__main__":
    unittest.main()
