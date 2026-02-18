"""GitHub profile importer using public API."""

import requests
from typing import Optional


class GitHubProfileImporter:
    """Import profile data from GitHub (public API, no auth needed)."""

    API_BASE = "https://api.github.com"

    def import_profile(self, github_url: str) -> dict:
        """
        Import profile from GitHub URL or username.
        Returns dict with name, bio, repos, languages, contributions.
        """
        # Extract username from URL or use directly
        username = github_url.strip().rstrip('/')
        if 'github.com/' in username:
            username = username.split('github.com/')[-1].split('/')[0]

        print(f"Fetching GitHub profile for: {username}")

        profile = {
            "username": username,
            "name": "",
            "bio": "",
            "company": "",
            "location": "",
            "blog": "",
            "repos": [],
            "languages": set(),
            "total_stars": 0,
        }

        try:
            # Get user profile
            user_resp = requests.get(
                f"{self.API_BASE}/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )

            if user_resp.status_code == 200:
                user = user_resp.json()
                profile["name"] = user.get("name", "")
                profile["bio"] = user.get("bio", "")
                profile["company"] = user.get("company", "")
                profile["location"] = user.get("location", "")
                profile["blog"] = user.get("blog", "")
                profile["public_repos"] = user.get("public_repos", 0)
                profile["followers"] = user.get("followers", 0)

            # Get top repositories
            repos_resp = requests.get(
                f"{self.API_BASE}/users/{username}/repos",
                params={"sort": "updated", "per_page": 10},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )

            if repos_resp.status_code == 200:
                repos = repos_resp.json()
                for repo in repos:
                    if not repo.get("fork"):  # Skip forks
                        profile["repos"].append({
                            "name": repo.get("name", ""),
                            "description": repo.get("description", ""),
                            "language": repo.get("language", ""),
                            "stars": repo.get("stargazers_count", 0),
                        })
                        if repo.get("language"):
                            profile["languages"].add(repo["language"])
                        profile["total_stars"] += repo.get("stargazers_count", 0)

            profile["languages"] = list(profile["languages"])

        except Exception as e:
            print(f"Error fetching GitHub profile: {e}")

        return profile

    def format_as_text(self, profile: dict) -> str:
        """Convert profile dict to readable text format."""
        lines = []

        if profile.get("name"):
            lines.append(f"GitHub: {profile['name']} (@{profile['username']})")
        else:
            lines.append(f"GitHub: @{profile['username']}")

        if profile.get("bio"):
            lines.append(profile["bio"])

        if profile.get("company"):
            lines.append(f"Company: {profile['company']}")

        lines.append("")

        if profile.get("languages"):
            lines.append(f"Languages: {', '.join(profile['languages'])}")

        stats = []
        if profile.get("public_repos"):
            stats.append(f"{profile['public_repos']} repos")
        if profile.get("total_stars"):
            stats.append(f"{profile['total_stars']} stars")
        if profile.get("followers"):
            stats.append(f"{profile['followers']} followers")
        if stats:
            lines.append(f"Stats: {', '.join(stats)}")

        lines.append("")

        if profile.get("repos"):
            lines.append("TOP PROJECTS")
            for repo in profile["repos"][:5]:
                stars = f" ({repo['stars']} stars)" if repo['stars'] else ""
                lang = f" [{repo['language']}]" if repo['language'] else ""
                lines.append(f"- {repo['name']}{lang}{stars}")
                if repo.get("description"):
                    lines.append(f"  {repo['description'][:100]}")

        return "\n".join(lines)
