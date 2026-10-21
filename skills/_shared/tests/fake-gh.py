#!/usr/bin/env python3
"""Offline stand-in for `gh` used by the skill tests. State: FAKE_GH_STATE (JSON); every call is appended to
FAKE_GH_LOG as {"args", "stdin", "write"}. Issue "author" defaults to state["viewer"]. Fault injection: state["fail"] =
[{"match": "<substring of args+stdin>", "times", "stderr", "code", optional "stdout" / "headers" / "status"}].
Crash: state["die"] = [{"match", "times", "when": "after"|"before"}] SIGKILLs the skill after (before) the write.
With `--include` (like `gh api --include`) a status line + headers + blank line come before the body."""
import json
import os
import re
import signal
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_gh_project_items import (GqlError, add_project_item, auto_add_sub_issue,  # noqa: E402
                                   items_by_id, listed_items)

STATE, LOG = os.environ["FAKE_GH_STATE"], os.environ["FAKE_GH_LOG"]
viewer = lambda st: st.get("viewer", "example-org")  # noqa: E731  (logged-in account = owner of REPO; default author)


def emit(args, body, status="200 OK", headers=None):
    hs = dict({"Content-Type": "application/json; charset=utf-8"}, **(headers or {}))
    head = "HTTP/2.0 %s\r\n%s\r\n" % (status, "".join("%s: %s\r\n" % kv for kv in hs.items()))
    sys.stdout.write((head if "--include" in args else "") + body)


def gql_fields(proj):
    nodes = []
    for name, f in proj["fields"].items():
        dt = {"single_select": "SINGLE_SELECT", "iteration": "ITERATION", "number": "NUMBER", "text": "TEXT"}[f["type"]]
        n = {"id": f["id"], "name": name, "dataType": dt}
        if f["type"] == "single_select":
            n["options"] = [{"id": v, "name": k} for k, v in f["options"].items()]
        if f["type"] == "iteration":
            its = [{"id": v, "title": k, "startDate": "2030-01-0%d" % (i + 1), "duration": 14}
                   for i, (k, v) in enumerate(f["iterations"].items())]
            n["configuration"] = {"iterations": its, "completedIterations": []}
        nodes.append(n)
    return nodes


def issue_node(st, i):
    items = [{"id": it["id"], "project": {"id": st["project"]["id"]}}
             for it in st["project"]["items"] if it["issueNumber"] == i["number"]]
    return {"id": i["nodeId"], "databaseId": i["id"], "number": i["number"], "state": i["state"],
            "title": i["title"], "body": i["body"], "closedAt": i.get("closedAt"),
            "parent": {"number": i["parent"]} if i.get("parent") else None,
            "labels": {"nodes": [{"name": x} for x in i["labels"]]}, "projectItems": {"nodes": items},
            "repository": {"nameWithOwner": st["repo"]}, "author": {"login": i.get("author", viewer(st))}}


def page(seq, after, size):
    start = int(after or 0)
    chunk = seq[start:start + size]
    more = start + size < len(seq)
    return chunk, {"hasNextPage": more, "endCursor": str(start + size) if more else None}


def graphql(st, body):
    q, v = body["query"], body.get("variables") or {}
    proj, size = st["project"], st.get("page_size", 100)
    by_num = {i["number"]: i for i in st["issues"]}
    if "addProjectV2ItemById" in q:
        return add_project_item(st, next(i["number"] for i in st["issues"] if i["nodeId"] == v["c"]))
    if "updateProjectV2ItemFieldValue" in q or "clearProjectV2ItemFieldValue" in q:
        item = next(it for it in proj["items"] if it["id"] == v["i"])
        name, f = next((n, f) for n, f in proj["fields"].items() if f["id"] == v["f"])
        val = v.get("v")
        if val is None:
            item["values"].pop(name, None)
        elif "number" in val:
            item["values"][name] = val["number"]
        elif "singleSelectOptionId" in val:
            item["values"][name] = next(k for k, o in f["options"].items() if o == val["singleSelectOptionId"])
        elif "iterationId" in val:
            item["values"][name] = next(k for k, o in f["iterations"].items() if o == val["iterationId"])
        else:
            item["values"][name] = val.get("text")
        return {"x": {"projectV2Item": {"id": item["id"]}}}
    if "repository(owner" in q:
        nodes, info = page([issue_node(st, i) for i in st["issues"]], v.get("after"), size)
        return {"viewer": {"login": viewer(st)}, "repository": {"issues": {"pageInfo": info, "nodes": nodes}}}
    pnode = {"id": proj["id"], "title": proj["title"], "public": False}
    if "fields(first" in q:
        pnode["fields"] = {"nodes": gql_fields(proj) + [{"id": "T", "name": "Title", "dataType": "TITLE"}]}
    if "nodes(ids" in q:
        if "... on Issue" in q:
            return {"nodes": [issue_node(st, i) for i in st["issues"] if i["nodeId"] in v["ids"]]}
        return {"nodes": items_by_id(st, v["ids"])}
    if "items(first" in q:
        nodes, info = page(listed_items(st, lambda n: issue_node(st, by_num[n])), v.get("after"), size)
        pnode["items"] = {"pageInfo": info, "nodes": nodes}
    return {"repositoryOwner": {"projectV2": pnode}}


def rest(st, path, method, body):
    m = re.match(r"repos/[^/]+/[^/]+/(.*)$", path.split("?")[0])
    rest_path = m.group(1)
    by_num = {i["number"]: i for i in st["issues"]}
    if rest_path == "labels":
        if method == "GET":  # paginated like the real API (?per_page=&page=)
            q = urllib.parse.parse_qs(path.partition("?")[2])
            size, pg = int(q.get("per_page", ["30"])[0]), int(q.get("page", ["1"])[0])
            return [{"name": n} for n in st["labels"][(pg - 1) * size:pg * size]]
        st["labels"].append(body["name"])
        return {"name": body["name"]}
    if rest_path == "issues" and method == "POST":
        n = st.get("next_number", len(st["issues"]) + 1)
        st["next_number"] = n + 1
        issue = {"number": n, "id": 1000 + n, "nodeId": "I_%d" % n, "title": body["title"],
                 "body": body.get("body", ""), "state": "OPEN", "labels": sorted(body.get("labels", [])), "parent": None}
        st["issues"].append(issue)
        return {"number": n, "id": issue["id"], "node_id": issue["nodeId"], "html_url": "https://github.com/%s/issues/%d" % (st["repo"], n)}
    if rest_path.startswith("issues/comments/"):
        cid = int(rest_path.rsplit("/", 1)[1])
        hit = [c for c in st.get("comments", []) if c.get("id") == cid]
        if not hit:
            raise SystemExit("HTTP 404: Not Found")
        st["comments"] = [c for c in st["comments"] if c["id"] != cid or method != "DELETE"]
        return None if method == "DELETE" else hit[0]
    num = int(rest_path.split("/")[1])
    issue = by_num[num]
    if rest_path.endswith("/sub_issues"):
        child = next(i for i in st["issues"] if i["id"] == body["sub_issue_id"])
        if child.get("parent"):
            raise SystemExit("HTTP 422: sub-issue already has a parent")
        child["parent"] = num
        auto_add_sub_issue(st, child["number"], num)
        return {"number": num}
    if rest_path.endswith("/comments"):
        if method == "GET":
            q = urllib.parse.parse_qs(path.partition("?")[2])
            size, pg = int(q.get("per_page", ["30"])[0]), int(q.get("page", ["1"])[0])
            mine = [{"id": c["id"], "body": c["body"]} for c in st.get("comments", []) if c["number"] == num]
            return mine[(pg - 1) * size:pg * size]
        st["next_comment_id"] = st.get("next_comment_id", 500) + 1
        st.setdefault("comments", []).append({"id": st["next_comment_id"], "number": num, "body": body["body"]})
        return {"id": st["next_comment_id"]}
    if "/labels" in rest_path:
        if method == "DELETE":
            gone = urllib.parse.unquote(rest_path.split("/labels/")[1])  # real API takes the name percent-encoded
            issue["labels"] = [x for x in issue["labels"] if x != gone]
        else:
            issue["labels"] = sorted(set(issue["labels"]) | set(body["labels"]))
        return [{"name": x} for x in issue["labels"]]
    if method == "PATCH":
        for k in ("title", "body"):
            if k in body:
                issue[k] = body[k]
        if "state" in body:
            issue["state"] = body["state"].upper()
        return {"number": num}
    return {"number": num, "id": issue["id"], "node_id": issue["nodeId"]}


def main():
    args = sys.argv[1:]
    stdin = sys.stdin.read() if "--input" in args else ""
    st = json.load(open(STATE, encoding="utf-8"))
    method = args[args.index("--method") + 1] if "--method" in args else "GET"
    is_write = (method != "GET") or ("mutation" in stdin)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"args": args, "stdin": stdin, "write": is_write}, ensure_ascii=False) + "\n")
    hay = " ".join(args) + " " + stdin
    for f in st.get("fail", []):
        if f["times"] > 0 and f["match"] in hay:
            f["times"] -= 1
            json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(f.get("sleep", 0))  # optional: hang (timeout tests)
            emit(args, f.get("stdout", ""), f.get("status", "403 Forbidden" if f.get("code", 1) else "200 OK"), f.get("headers"))
            sys.stderr.write(f["stderr"])
            sys.exit(f.get("code", 1))
    die = next((d for d in st.get("die", []) if d["times"] > 0 and d["match"] in hay), None)
    if die:
        die["times"] -= 1
        json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
        if die.get("when") == "before":
            os.kill(os.getppid(), signal.SIGKILL)
            sys.exit(1)
    if args[:2] == ["api", "graphql"]:
        try:
            result = {"data": graphql(st, json.loads(stdin))}
        except GqlError as e:
            emit(args, json.dumps({"data": None, "errors": [{"type": e.kind, "message": str(e)}]}))
            sys.stderr.write(f"gh: {e}\n")
            sys.exit(1)
    else:
        result = rest(st, args[1], method, json.loads(stdin) if stdin else None)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    emit(args, "" if result is None else json.dumps(result, ensure_ascii=False), "204 No Content" if result is None else "200 OK")
    if die:  # the write reached "GitHub"; the skill dies before it can log the outcome
        os.kill(os.getppid(), signal.SIGKILL)


if __name__ == "__main__":
    main()
