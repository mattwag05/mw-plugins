#!/usr/bin/env python3
"""Search and discover Agent Skills from verified GitHub repositories.

Supports offline cache, gh CLI, and GITHUB_TOKEN for data access.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "skills_cache.json"

REPOS = [
    ("anthropics", "skills"),
    ("obra", "superpowers"),
    ("vercel-labs", "agent-skills"),
    ("K-Dense-AI", "claude-scientific-skills"),
    ("ComposioHQ", "awesome-claude-skills"),
    ("travisvn", "awesome-claude-skills"),
    ("BehiSecc", "awesome-claude-skills"),
]


def load_cache():
    """Load the offline skills cache."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return None


def has_gh_cli():
    """Check if gh CLI is available and authenticated."""
    return shutil.which("gh") is not None


def gh_api(endpoint, jq_filter=None):
    """Call GitHub API via gh CLI."""
    cmd = ["gh", "api", endpoint]
    if jq_filter:
        cmd.extend(["--jq", jq_filter])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def github_api_request(endpoint, token=None):
    """Call GitHub API via urllib with optional token."""
    url = f"https://api.github.com/{endpoint}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "internet-skill-finder"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def fetch_repo_stars_gh(owner, repo):
    """Fetch star count via gh CLI."""
    result = gh_api(f"repos/{owner}/{repo}", ".stargazers_count")
    if result:
        try:
            return int(result)
        except ValueError:
            pass
    return None


def fetch_skill_md_gh(owner, repo, path):
    """Fetch a SKILL.md file content via gh CLI."""
    # Try to get file content
    result = gh_api(
        f"repos/{owner}/{repo}/contents/{path}/SKILL.md",
        ".content"
    )
    if result:
        import base64
        try:
            return base64.b64decode(result).decode("utf-8")
        except Exception:
            pass
    return None


def fetch_skill_md_api(owner, repo, path, token=None):
    """Fetch a SKILL.md file content via GitHub API."""
    data = github_api_request(f"repos/{owner}/{repo}/contents/{path}/SKILL.md", token)
    if data and "content" in data:
        import base64
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except Exception:
            pass
    return None


def fetch_repo_online(owner, repo):
    """Fetch skill listing from a repo online."""
    use_gh = has_gh_cli()
    token = os.environ.get("GITHUB_TOKEN")

    # Get repo metadata
    stars = None
    description = None
    if use_gh:
        meta = gh_api(f"repos/{owner}/{repo}", '{stars: .stargazers_count, description: .description}')
        if meta:
            try:
                m = json.loads(meta)
                stars = m.get("stars")
                description = m.get("description")
            except json.JSONDecodeError:
                pass
    if stars is None and token:
        data = github_api_request(f"repos/{owner}/{repo}", token)
        if data:
            stars = data.get("stargazers_count")
            description = data.get("description")

    # Get tree to find SKILL.md files
    skills = []
    tree_data = None
    for branch in ["main", "master"]:
        if use_gh:
            raw = gh_api(
                f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                '[.tree[] | select(.path | test("SKILL\\\\.md$"; "i")) | .path]'
            )
            if raw:
                try:
                    tree_data = json.loads(raw)
                    break
                except json.JSONDecodeError:
                    pass
        if token:
            data = github_api_request(f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1", token)
            if data and "tree" in data:
                tree_data = [
                    item["path"] for item in data["tree"]
                    if item["path"].upper().endswith("SKILL.MD")
                ]
                break

    if tree_data:
        for skill_path in tree_data:
            # Extract skill name from path (parent directory)
            parts = skill_path.split("/")
            if len(parts) >= 2:
                skill_name = parts[-2]
                skill_dir = "/".join(parts[:-1])
                # Skip template skills
                if skill_name.lower() in ("template", "template-skill"):
                    continue
                skills.append({
                    "name": skill_name,
                    "path": skill_dir,
                    "description": "",
                    "tags": []
                })

    return {
        "owner": owner,
        "repo": repo,
        "stars": stars or 0,
        "description": description or "",
        "url": f"https://github.com/{owner}/{repo}",
        "type": "skill_repo",
        "skills": skills
    }


def search_skills(query, data, limit=20):
    """Search skills by keyword across all repos."""
    query_lower = query.lower()
    query_terms = query_lower.split()
    results = []

    for repo in data.get("repositories", []):
        for skill in repo.get("skills", []):
            score = 0
            name = skill.get("name", "").lower()
            desc = skill.get("description", "").lower()
            tags = [t.lower() for t in skill.get("tags", [])]

            for term in query_terms:
                # Exact name match is highest priority
                if term == name:
                    score += 100
                elif term in name:
                    score += 50
                # Tag match
                if term in tags:
                    score += 30
                # Description match
                if term in desc:
                    score += 10
                # Partial tag match
                for tag in tags:
                    if term in tag or tag in term:
                        score += 5

            if score > 0:
                results.append({
                    "skill": skill,
                    "repo_owner": repo["owner"],
                    "repo_name": repo["repo"],
                    "repo_stars": repo.get("stars", 0),
                    "repo_url": repo["url"],
                    "score": score
                })

    # Sort by score descending, then by repo stars
    results.sort(key=lambda x: (-x["score"], -x["repo_stars"]))
    return results[:limit]


def list_all_skills(data):
    """List all skills grouped by repository."""
    output = []
    for repo in data.get("repositories", []):
        repo_skills = repo.get("skills", [])
        if repo_skills:
            output.append({
                "repo": f"{repo['owner']}/{repo['repo']}",
                "stars": repo.get("stars", 0),
                "url": repo["url"],
                "type": repo.get("type", "unknown"),
                "skill_count": len(repo_skills),
                "skills": [
                    {"name": s["name"], "description": s.get("description", "")}
                    for s in repo_skills
                ]
            })
    return output


def deep_dive(owner_repo, skill_name, data, online=False):
    """Get detailed information about a specific skill."""
    parts = owner_repo.split("/")
    if len(parts) != 2:
        return {"error": f"Invalid repo format: {owner_repo}. Use 'owner/repo'."}

    owner, repo = parts

    # Find the skill in cache
    skill_info = None
    repo_info = None
    for r in data.get("repositories", []):
        if r["owner"] == owner and r["repo"] == repo:
            repo_info = r
            for s in r.get("skills", []):
                if s["name"] == skill_name:
                    skill_info = s
                    break
            break

    if not skill_info:
        return {"error": f"Skill '{skill_name}' not found in {owner_repo}."}

    result = {
        "name": skill_info["name"],
        "repo": owner_repo,
        "stars": repo_info.get("stars", 0) if repo_info else 0,
        "path": skill_info.get("path", ""),
        "description": skill_info.get("description", ""),
        "tags": skill_info.get("tags", []),
        "github_url": f"https://github.com/{owner}/{repo}/tree/main/{skill_info.get('path', '')}",
    }

    # If external skill, include external URL
    if "external_url" in skill_info:
        result["github_url"] = skill_info["external_url"]

    # Try to fetch SKILL.md content if online
    if online:
        skill_md = None
        if has_gh_cli():
            skill_md = fetch_skill_md_gh(owner, repo, skill_info.get("path", ""))
        if not skill_md:
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                skill_md = fetch_skill_md_api(owner, repo, skill_info.get("path", ""), token)
        if skill_md:
            result["skill_md_content"] = skill_md

    return result


def check_rate_limit():
    """Check GitHub API rate limit status."""
    result = {}

    if has_gh_cli():
        raw = gh_api("rate_limit", '{rate: .rate, graphql: .resources.graphql}')
        if raw:
            try:
                result["gh_cli"] = json.loads(raw)
                result["gh_cli"]["method"] = "gh CLI (authenticated)"
            except json.JSONDecodeError:
                result["gh_cli"] = {"error": "Could not parse rate limit"}
    else:
        result["gh_cli"] = {"available": False, "message": "gh CLI not installed or not authenticated"}

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        data = github_api_request("rate_limit", token)
        if data:
            result["token"] = {
                "method": "GITHUB_TOKEN",
                "rate": data.get("rate", {}),
            }
    else:
        result["token"] = {"available": False, "message": "GITHUB_TOKEN not set"}

    # Check unauthenticated
    data = github_api_request("rate_limit")
    if data:
        result["unauthenticated"] = {
            "method": "unauthenticated",
            "rate": data.get("rate", {}),
        }

    return result


def format_results_text(results, using_cache=True):
    """Format search results as human-readable text."""
    if not results:
        return "No matching skills found."

    lines = []
    if using_cache:
        lines.append("(Results from cached data. Use --online for real-time results.)\n")

    for i, r in enumerate(results, 1):
        skill = r["skill"]
        name = skill.get("name", "unknown")
        desc = skill.get("description", "No description available.")
        repo = f"{r['repo_owner']}/{r['repo_name']}"
        stars = r.get("repo_stars", 0)
        tags = ", ".join(skill.get("tags", []))

        # Build GitHub URL for this skill
        path = skill.get("path", "")
        if "external_url" in skill:
            url = skill["external_url"]
        else:
            branch = "main"
            if r["repo_owner"] == "ComposioHQ":
                branch = "master"
            url = f"https://github.com/{repo}/tree/{branch}/{path}"

        lines.append(f"### {i}. {name}")
        lines.append(f"**Source**: {repo} | Stars: {stars:,}")
        lines.append(f"**Description**: {desc}")
        if tags:
            lines.append(f"**Tags**: {tags}")
        lines.append(f"**URL**: {url}")
        lines.append("")

    return "\n".join(lines)


def format_list_text(repo_list, using_cache=True):
    """Format skill listing as human-readable text."""
    lines = []
    if using_cache:
        lines.append("(Results from cached data. Use --online for real-time results.)\n")

    total = sum(r["skill_count"] for r in repo_list)
    lines.append(f"Total: {total} skills across {len(repo_list)} repositories\n")

    for repo in repo_list:
        lines.append(f"## {repo['repo']} (Stars: {repo['stars']:,}, {repo['skill_count']} skills)")
        lines.append(f"   Type: {repo['type']} | {repo['url']}")
        for s in repo["skills"]:
            desc = s["description"][:80] + "..." if len(s.get("description", "")) > 80 else s.get("description", "")
            lines.append(f"   - {s['name']}: {desc}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search Agent Skills across verified GitHub repositories"
    )
    parser.add_argument("--search", "-s", metavar="QUERY", help="Search skills by keyword")
    parser.add_argument("--list", "-l", action="store_true", help="List all available skills")
    parser.add_argument("--deep-dive", "-d", nargs=2, metavar=("OWNER/REPO", "SKILL"),
                        help="Get detailed info about a specific skill")
    parser.add_argument("--online", action="store_true",
                        help="Force real-time fetch from GitHub (requires network)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--rate-limit", action="store_true", help="Check GitHub API rate limits")
    parser.add_argument("--limit", type=int, default=20, help="Max results for search (default: 20)")
    parser.add_argument("--refresh-cache", action="store_true",
                        help="Fetch fresh data from GitHub and update the offline cache")

    args = parser.parse_args()

    # Rate limit check
    if args.rate_limit:
        limits = check_rate_limit()
        if args.json:
            print(json.dumps(limits, indent=2))
        else:
            print("GitHub API Rate Limits:")
            for method, info in limits.items():
                print(f"\n  {method}:")
                if isinstance(info, dict):
                    for k, v in info.items():
                        print(f"    {k}: {v}")
        return

    # Determine data source
    using_cache = True
    data = None

    if args.online or args.refresh_cache:
        # Try online fetch
        print("Fetching live data from GitHub...", file=sys.stderr)
        repos_data = []
        for owner, repo in REPOS:
            print(f"  Fetching {owner}/{repo}...", file=sys.stderr)
            repo_data = fetch_repo_online(owner, repo)
            repos_data.append(repo_data)

        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_skills": sum(len(r["skills"]) for r in repos_data),
            "repositories": repos_data
        }
        using_cache = False

        if args.refresh_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Cache updated: {CACHE_FILE}", file=sys.stderr)
    else:
        data = load_cache()
        if not data:
            print("Error: No cache file found. Run with --online or --refresh-cache first.",
                  file=sys.stderr)
            sys.exit(1)

    # Execute requested action
    if args.search:
        results = search_skills(args.search, data, limit=args.limit)
        if args.json:
            print(json.dumps({"query": args.search, "using_cache": using_cache,
                              "result_count": len(results), "results": results}, indent=2))
        else:
            print(format_results_text(results, using_cache))

    elif args.list:
        repo_list = list_all_skills(data)
        if args.json:
            print(json.dumps({"using_cache": using_cache, "repositories": repo_list}, indent=2))
        else:
            print(format_list_text(repo_list, using_cache))

    elif args.deep_dive:
        owner_repo, skill_name = args.deep_dive
        result = deep_dive(owner_repo, skill_name, data, online=args.online)
        if args.json:
            print(json.dumps({"using_cache": using_cache, **result}, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"## {result['name']}")
                print(f"**Repository**: {result['repo']} | Stars: {result.get('stars', 0):,}")
                print(f"**Path**: {result['path']}")
                print(f"**Description**: {result['description']}")
                if result.get("tags"):
                    print(f"**Tags**: {', '.join(result['tags'])}")
                print(f"**GitHub URL**: {result['github_url']}")
                if result.get("skill_md_content"):
                    print(f"\n--- SKILL.md Content ---\n")
                    print(result["skill_md_content"])

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
