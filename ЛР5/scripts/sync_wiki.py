"""Create or update the LR5 Markdown pages in the local Wiki.js instance."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8085/graphql"


def env_values():
    return dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
        if "=" in line
    )


def graphql(query, variables=None, jwt=None):
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    request = Request(
        URL,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers=headers,
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result["data"]


def wiki_content(filename):
    content = (ROOT / filename).read_text(encoding="utf-8")
    for name in ("GDD", "SRS", "SDD"):
        content = content.replace(f"({name}.md)", f"(/alien-invasion/{name.lower()})")
    return content


def main():
    values = env_values()
    login = graphql(
        'mutation($u:String!,$p:String!){authentication{login(username:$u,password:$p,strategy:"local"){jwt responseResult{succeeded message}}}}',
        {"u": values["WIKI_ADMIN_EMAIL"], "p": values["WIKI_ADMIN_PASSWORD"]},
    )["authentication"]["login"]
    if not login["responseResult"]["succeeded"]:
        raise RuntimeError(login["responseResult"]["message"])
    jwt = login["jwt"]
    existing = {
        page["path"]: page["id"]
        for page in graphql("{pages{list{id path}}}", jwt=jwt)["pages"]["list"]
    }
    pages = [
        ("alien-invasion/gdd", "Game Design Document (GDD) for Alien Invasion", wiki_content("GDD.md")),
        ("alien-invasion/srs", "Software Requirements Specification (SRS) for Alien Invasion", wiki_content("SRS.md")),
        ("alien-invasion/sdd", "Software Design Document (SDD) for Alien Invasion", wiki_content("SDD.md")),
        (
            "home",
            "ЛР5 — Alien Invasion",
            "# ЛР5 — Alien Invasion\n\n"
            "Проектная документация игры и план задач:\n\n"
            "- [GDD](/alien-invasion/gdd) — игровой дизайн.\n"
            "- [SRS](/alien-invasion/srs) — требования.\n"
            "- [SDD](/alien-invasion/sdd) — проектное решение.\n"
            "- [Проект в Redmine](http://localhost:3005/projects/alien-invasion-game) — задачи разработки.\n",
        ),
    ]
    create = """mutation($content:String!,$description:String!,$path:String!,$title:String!){
      pages{create(content:$content,description:$description,editor:"markdown",
        isPublished:true,isPrivate:false,locale:"en",path:$path,tags:[],title:$title){
          responseResult{succeeded message errorCode} page{id path title}
      }}
    }"""
    update = """mutation($id:Int!,$content:String!,$description:String!,$path:String!,$title:String!){
      pages{update(id:$id,content:$content,description:$description,editor:"markdown",
        isPublished:true,isPrivate:false,locale:"en",path:$path,tags:[],title:$title){
          responseResult{succeeded message errorCode} page{id path title}
      }}
    }"""
    for path, title, content in pages:
        variables = {"content": content, "description": title, "path": path, "title": title}
        if path in existing:
            variables["id"] = existing[path]
            result = graphql(update, variables, jwt)["pages"]["update"]
            action = "updated"
        else:
            result = graphql(create, variables, jwt)["pages"]["create"]
            action = "created"
        if not result["responseResult"]["succeeded"]:
            raise RuntimeError(f"{path}: {result['responseResult']}")
        print(f"{action}: http://localhost:8085/{path}")


if __name__ == "__main__":
    main()
