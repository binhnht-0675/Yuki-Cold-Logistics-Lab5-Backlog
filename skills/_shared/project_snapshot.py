"""Read every Project item with its field values (read-only) -> snapshot dict.

The snapshot holds no issue bodies. Keys come from the key map (number -> key).
With `repo`, only that repository's issues are kept (compared case-insensitively) and keys are looked up
by "repo#number" only, so issue #1 of another repository can never take the key of our #1. Without
`repo`, a Project that holds issues of more than one repository is refused.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Dict, List, Optional

from gh_runner import GhRunner
from project_fields import project_node

FIELD_NAME = "field { ... on ProjectV2FieldCommon { name } }"
FIELD_VALUES = """fieldValues(first:30) { nodes {
        ... on ProjectV2ItemFieldSingleSelectValue { name %(f)s }
        ... on ProjectV2ItemFieldNumberValue { number %(f)s }
        ... on ProjectV2ItemFieldIterationValue { title %(f)s }
        ... on ProjectV2ItemFieldTextValue { text %(f)s }
        ... on ProjectV2ItemFieldDateValue { date %(f)s }
      } }""" % {"f": FIELD_NAME}
ITEMS_QUERY = """
query($owner:String!, $number:Int!, $after:String) {
  repositoryOwner(login:$owner) {
    ... on User { projectV2(number:$number) { ...P } }
    ... on Organization { projectV2(number:$number) { ...P } }
  }
}
fragment P on ProjectV2 {
  id title
  items(first:100, after:$after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      %(v)s
      content { ... on Issue {
        id number title state closedAt
        repository { nameWithOwner }
        parent { number }
        labels(first:30) { nodes { name } }
      } }
    }
  }
}""" % {"v": FIELD_VALUES}

# GitHub's item list of a Project can lag minutes behind items just added through the API (trial push
# 20/10: 1 of 15 listed). Items whose id is already known are read directly, by id.
ITEMS_BY_ID_QUERY = """
query($ids:[ID!]!) { nodes(ids:$ids) { ... on ProjectV2Item { id %(v)s } } }""" % {"v": FIELD_VALUES}
BY_ID_BATCH = 50

SKIP_FIELDS = {"Title", "Labels", "Repository", "Assignees", "Milestone", "Parent issue",
               "Sub-issues progress", "Linked pull requests", "Reviewers"}


def _value(node: dict) -> Any:
    for k in ("name", "number", "title", "text", "date"):
        if k in node:
            return node[k]
    return None


def _fields(node: dict) -> Dict[str, Any]:
    fields = {}
    for fv in (node.get("fieldValues") or {}).get("nodes") or []:
        name = ((fv or {}).get("field") or {}).get("name")
        if name and name not in SKIP_FIELDS:
            fields[name] = _value(fv)
    return fields


def read_item_fields(runner: GhRunner, item_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """{item id: field values} read by id (for items the Project's item list does not show yet)."""
    out: Dict[str, Dict[str, Any]] = {}
    for i in range(0, len(item_ids), BY_ID_BATCH):
        data = runner.graphql(ITEMS_BY_ID_QUERY, {"ids": item_ids[i:i + BY_ID_BATCH]})
        for node in (data.get("nodes") or []):
            if node and node.get("id"):
                out[node["id"]] = _fields(node)
    missing = [i for i in item_ids if i not in out]
    if missing:
        raise ValueError(f"Project のアイテム {len(missing)} 件が id で読めません（例: {missing[0]}）。"
                         "Project から外された可能性。rebuild-key-map で確かめてください")
    return out


def parse_item(node: dict, key_by_number: Dict[str, str], by_repo: bool = False) -> Optional[dict]:
    content = node.get("content") or {}
    if "number" not in content:
        return None  # draft issue / pull request: outside the backlog
    fields = _fields(node)
    repo = (content.get("repository") or {}).get("nameWithOwner")
    key = key_by_number.get(f"{(repo or '').lower()}#{content['number']}")
    if not by_repo:
        key = key or key_by_number.get(str(content["number"]))
    return {
        "itemId": node["id"], "nodeId": content.get("id"), "number": content["number"], "repo": repo,
        "key": key,
        "title": content.get("title"), "state": content.get("state"), "closedAt": content.get("closedAt"),
        "parentNumber": (content.get("parent") or {}).get("number"),
        "labels": sorted(n["name"] for n in ((content.get("labels") or {}).get("nodes") or [])),
        "fields": fields,
    }


def key_index(key_map: Dict[str, dict], repo: Optional[str]) -> Dict[str, str]:
    """repo known: only "owner/name#N" (lower-case) keys; no repo: bare "N" keys too."""
    idx = {}
    for key, entry in key_map.items():
        if repo:
            idx[f"{repo.lower()}#{entry['number']}"] = key
        else:
            idx[str(entry["number"])] = key
    return idx


def read_snapshot(runner: GhRunner, owner: str, number: int, key_map: Dict[str, dict],
                  repo: Optional[str] = None) -> Dict[str, Any]:
    idx = key_index(key_map, repo)
    after, items, title, pid = None, [], None, None
    while True:
        node = project_node(runner.graphql(ITEMS_QUERY, {"owner": owner, "number": number, "after": after}))
        title, pid = node.get("title"), node.get("id")
        conn = node["items"]
        items.extend(i for i in (parse_item(n, idx, bool(repo)) for n in conn["nodes"]) if i)
        if not conn["pageInfo"]["hasNextPage"]:
            break
        after = conn["pageInfo"]["endCursor"]
    repos = sorted({(i["repo"] or "").lower() for i in items})
    excluded = 0
    if repo:
        kept = [i for i in items if (i["repo"] or "").lower() == repo.lower()]
        excluded, items = len(items) - len(kept), kept
    elif len(repos) > 1:
        raise ValueError(f"Project に複数リポジトリの issue があります（{', '.join(repos[:5])}）。--repo を指定してください")
    items.sort(key=lambda i: (i["repo"] or "", i["number"]))
    return {
        "takenAt": _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "owner": owner, "project": number, "projectId": pid, "title": title, "repo": repo,
        "excludedOtherRepo": excluded, "items": items,
    }


def load_snapshot(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_snapshot(path: str, snap: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def leaf_items(items: List[dict]) -> List[dict]:
    """Items that are nobody's parent (inside the same snapshot)."""
    parents = {i["parentNumber"] for i in items if i.get("parentNumber")}
    return [i for i in items if i["number"] not in parents]
