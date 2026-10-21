"""add_item on "Content already exists in this project" (Project workflow Auto-add sub-issues, 20/10):
take the existing item only when it belongs to THIS Project; otherwise the error stands."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gh_runner import GhError  # noqa: E402
from project_fields import add_item  # noqa: E402


class StubRunner:
    def __init__(self, items):
        self.items, self.calls = items, []

    def graphql(self, query, variables=None, write=False):
        self.calls.append(query)
        if "addProjectV2ItemById" in query:
            raise GhError(["api", "graphql"], 1, "gh: Content already exists in this project")
        return {"nodes": [{"projectItems": {"nodes": self.items}}]}


class AddItemAlreadyExistsTest(unittest.TestCase):
    def test_existing_item_of_this_project_is_used(self):
        r = StubRunner([{"id": "PVTI_other", "project": {"id": "PVT_other"}},
                        {"id": "PVTI_mine", "project": {"id": "PVT_mine"}}])
        self.assertEqual(add_item(r, "PVT_mine", "I_1"), "PVTI_mine")

    def test_item_only_in_another_project_keeps_the_error(self):
        r = StubRunner([{"id": "PVTI_other", "project": {"id": "PVT_other"}}])
        with self.assertRaises(GhError):
            add_item(r, "PVT_mine", "I_1")


if __name__ == "__main__":
    unittest.main()
