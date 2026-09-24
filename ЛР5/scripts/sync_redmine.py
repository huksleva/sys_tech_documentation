"""Create the LR5 project and issues in the local Redmine instance."""

import base64
import csv
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:3005"
PROJECT = "alien-invasion-game"


def env_values():
    return dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
        if "=" in line
    )


def request(path, auth, method="GET", body=None):
    headers = {"Authorization": "Basic " + auth, "Content-Type": "application/json"}
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except HTTPError as error:
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:500]}") from error


def main():
    values = env_values()
    auth = base64.b64encode(("admin:" + values["REDMINE_ADMIN_PASSWORD"]).encode()).decode()
    user = request("/users/current.json", auth)["user"]
    trackers = request("/trackers.json", auth)["trackers"]
    roles = request("/roles.json", auth)["roles"]
    feature = next(t for t in trackers if t["name"] == "Feature")
    manager = next(r for r in roles if r["name"] == "Manager")

    projects = request("/projects.json?limit=100", auth)["projects"]
    project = next((p for p in projects if p["identifier"] == PROJECT), None)
    if project is None:
        project = request(
            "/projects.json",
            auth,
            "POST",
            {"project": {
                "name": "Alien Invasion Game",
                "identifier": PROJECT,
                "description": "План базовой версии игры Alien Invasion для ЛР5. Требования: http://localhost:8085/alien-invasion/srs",
                "is_public": False,
                "tracker_ids": [feature["id"]],
                "enabled_module_names": ["issue_tracking", "wiki", "files"],
            }},
        )["project"]
        print(f"created project: {BASE}/projects/{PROJECT}")
    else:
        print(f"project exists: {BASE}/projects/{PROJECT}")

    members = request(f"/projects/{PROJECT}/memberships.json", auth)["memberships"]
    if not any(m.get("user", {}).get("id") == user["id"] for m in members):
        request(
            f"/projects/{PROJECT}/memberships.json",
            auth,
            "POST",
            {"membership": {"user_id": user["id"], "role_ids": [manager["id"]]}},
        )
        print(f"assigned project member: {user['firstname']} {user['lastname']}")

    issues = request(f"/issues.json?project_id={project['id']}&status_id=*&limit=100", auth)["issues"]
    existing = {issue["subject"] for issue in issues}
    with (ROOT / "REDMINE_TASKS.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row["Тема"] in existing:
            continue
        description = (
            row["Описание"] + "\n\n"
            + "Требования: " + row["Требования"] + "\n"
            + "Критерий готовности: " + row["Критерий готовности"] + "\n"
            + "SRS: http://localhost:8085/alien-invasion/srs\n"
            + "SDD: http://localhost:8085/alien-invasion/sdd"
        )
        created = request(
            "/issues.json",
            auth,
            "POST",
            {"issue": {
                "project_id": project["id"],
                "tracker_id": feature["id"],
                "subject": row["Тема"],
                "description": description,
                "assigned_to_id": user["id"],
            }},
        )["issue"]
        print(f"created issue #{created['id']}: {row['Тема']}")

    final = request(f"/issues.json?project_id={project['id']}&status_id=*&limit=100", auth)["issues"]
    assigned = sum(i.get("assigned_to", {}).get("id") == user["id"] for i in final)
    print(f"verified: {len(final)} issues, {assigned} assigned to {user['firstname']} {user['lastname']}")
    if len(final) < 10 or assigned != len(final):
        raise RuntimeError("Project does not yet meet the issue count or assignment requirement")


if __name__ == "__main__":
    main()
