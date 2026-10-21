"""Project (v2) field map: read field / option / iteration IDs, write one item value."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from gh_runner import GhError, GhRunner

FIELDS_QUERY = """
query($owner:String!, $number:Int!) {
  repositoryOwner(login:$owner) {
    ... on User { projectV2(number:$number) { ...P } }
    ... on Organization { projectV2(number:$number) { ...P } }
  }
}
fragment P on ProjectV2 {
  id title public
  fields(first:50) { nodes {
    ... on ProjectV2FieldCommon { id name dataType }
    ... on ProjectV2SingleSelectField { options { id name } }
    ... on ProjectV2IterationField { configuration {
      iterations { id title startDate duration }
      completedIterations { id title startDate duration } } }
  } }
}"""

UPDATE_MUTATION = """
mutation($p:ID!, $i:ID!, $f:ID!, $v:ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:$v}) { projectV2Item { id } }
}"""

CLEAR_MUTATION = """
mutation($p:ID!, $i:ID!, $f:ID!) {
  clearProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f}) { projectV2Item { id } }
}"""

ADD_ITEM_MUTATION = """
mutation($p:ID!, $c:ID!) {
  addProjectV2ItemById(input:{projectId:$p, contentId:$c}) { item { id } }
}"""

TYPE_BY_DATATYPE = {"SINGLE_SELECT": "single_select", "ITERATION": "iteration",
                    "NUMBER": "number", "TEXT": "text", "DATE": "date"}


def project_node(data: dict) -> dict:
    owner = data.get("repositoryOwner") or {}
    node = owner.get("projectV2")
    if not node:
        raise ValueError("Project が見つかりません（owner / number / 権限を確認）")
    return node


def fetch_field_map(runner: GhRunner, owner: str, number: int) -> Dict[str, Any]:
    node = project_node(runner.graphql(FIELDS_QUERY, {"owner": owner, "number": number}))
    fields: Dict[str, Any] = {}
    for f in node["fields"]["nodes"]:
        kind = TYPE_BY_DATATYPE.get(f.get("dataType", ""))
        if not kind or "id" not in f:
            continue  # built-in fields (Title, Assignees, Labels, ...) are not writable here
        entry: Dict[str, Any] = {"id": f["id"], "type": kind}
        if kind == "single_select":
            entry["options"] = {o["name"]: o["id"] for o in f.get("options", [])}
        if kind == "iteration":
            conf = f.get("configuration") or {}
            its = (conf.get("iterations") or []) + (conf.get("completedIterations") or [])
            entry["iterations"] = {i["title"]: i["id"] for i in its}
            entry["iterationDates"] = {i["title"]: [i["startDate"], i["duration"]] for i in its}
        fields[f["name"]] = entry
    return {"owner": owner, "number": number, "projectId": node["id"], "title": node.get("title"),
            "public": node.get("public"), "fields": fields}


def load_field_map(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_field_map(path: str, fmap: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fmap, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def encode_value(fmap: Dict[str, Any], field: str, value: Any) -> Optional[dict]:
    """Translate a human value (option name, iteration title, number) to a GraphQL value.

    Returns None for "clear". Raises KeyError/ValueError for unknown field/option.
    """
    spec = fmap["fields"][field]
    if value is None or value == "":
        return None
    kind = spec["type"]
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field}: 数値ではありません: {value!r}")
        return {"number": float(value)}
    if kind == "single_select":
        if value not in spec["options"]:
            raise ValueError(f"{field}: 選択肢にない値: {value!r}")
        return {"singleSelectOptionId": spec["options"][value]}
    if kind == "iteration":
        if value not in spec["iterations"]:
            raise ValueError(f"{field}: イテレーションにない値: {value!r}")
        return {"iterationId": spec["iterations"][value]}
    if kind == "text":
        return {"text": str(value)}
    if kind == "date":
        return {"date": str(value)}
    raise ValueError(f"{field}: 未対応の型 {kind}")


def set_item_field(runner: GhRunner, fmap: Dict[str, Any], item_id: str, field: str, value: Any) -> None:
    enc = encode_value(fmap, field, value)
    base = {"p": fmap["projectId"], "i": item_id, "f": fmap["fields"][field]["id"]}
    if enc is None:
        runner.graphql(CLEAR_MUTATION, base, write=True)
    else:
        runner.graphql(UPDATE_MUTATION, dict(base, v=enc), write=True)


ITEM_OF_ISSUE_QUERY = """
query($ids:[ID!]!) { nodes(ids:$ids) { ... on Issue { projectItems(first:20) { nodes { id project { id } } } } } }"""
ALREADY_IN_PROJECT = "Content already exists in this project"


def add_item(runner: GhRunner, project_id: str, content_node_id: str) -> str:
    """Add an issue to the Project and return its item id. The Project workflow "Auto-add sub-issues to
    project" may have added it already (seen 20/10 right after the sub-issue link): GitHub then refuses the
    add, and the item that is already there is used."""
    try:
        data = runner.graphql(ADD_ITEM_MUTATION, {"p": project_id, "c": content_node_id}, write=True)
    except GhError as e:
        if ALREADY_IN_PROJECT not in str(e):
            raise
        nodes = runner.graphql(ITEM_OF_ISSUE_QUERY, {"ids": [content_node_id]})["nodes"]
        items = ((nodes[0] or {}).get("projectItems") or {}).get("nodes") or [] if nodes else []
        hit = next((n["id"] for n in items if (n.get("project") or {}).get("id") == project_id), None)
        if not hit:
            raise
        return hit
    return data["addProjectV2ItemById"]["item"]["id"]
