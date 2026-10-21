"""Project items for fake-gh.py: the paged `items(first…)` list and `nodes(ids:…)` look-ups.

GitHub's list of a Project's items can lag behind items just added through the API (seen 20/10: 15 items
added, the list showed 1, then 2, then 3 a minute later, while every issue already had its item). The fake
mimics that with state["unlisted_items"]: item ids left out of the list but still found by id.
"""


def field_value(name, f, v):
    key = {"single_select": "name", "number": "number", "iteration": "title", "text": "text"}[f["type"]]
    return {key: v, "field": {"name": name}}


def item_node(proj, it, content=None):
    node = {"id": it["id"], "fieldValues": {"nodes": [field_value(n, proj["fields"][n], x)
                                                      for n, x in it["values"].items()]}}
    if content is not None:
        node["content"] = content
    return node


def listed_items(st, content_of):
    hidden = set(st.get("unlisted_items") or [])
    proj = st["project"]
    return [item_node(proj, it, content_of(it["issueNumber"])) for it in proj["items"] if it["id"] not in hidden]


def items_by_id(st, ids):
    """state["unreadable_items"]: ids GitHub answers with null (e.g. removed from the Project meanwhile)."""
    proj, gone = st["project"], set(st.get("unreadable_items") or [])
    found = {it["id"]: it for it in proj["items"] if it["id"] not in gone}
    return [item_node(proj, found[i]) if i in found else None for i in ids]


class GqlError(Exception):
    """A GraphQL error answer (gh prints the body, exits 1)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def add_project_item(st, num):
    """addProjectV2ItemById. With state["auto_add_sub_issues"] (the Project workflow seen 20/10 on GitHub), a
    second add of the same content is refused with UNPROCESSABLE, as GitHub does."""
    proj = st["project"]
    hit = next((it for it in proj["items"] if it["issueNumber"] == num), None)
    if hit and st.get("auto_add_sub_issues"):
        raise GqlError("UNPROCESSABLE", "Content already exists in this project")
    if not hit:
        hit = {"id": "PVTI_%d" % num, "issueNumber": num, "values": {}}
        proj["items"].append(hit)
    return {"addProjectV2ItemById": {"item": {"id": hit["id"]}}}


def auto_add_sub_issue(st, child_num, parent_num):
    """Workflow "Auto-add sub-issues to project": a new sub-issue of an item in the Project is added too."""
    items = st["project"]["items"]
    if st.get("auto_add_sub_issues") and any(it["issueNumber"] == parent_num for it in items) \
            and not any(it["issueNumber"] == child_num for it in items):
        items.append({"id": "PVTI_%d" % child_num, "issueNumber": child_num, "values": {}})
