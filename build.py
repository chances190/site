#!/usr/bin/env python3
"""Minimal static site generator."""

import re
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime


class Builder:
    def __init__(self):
        self.root = Path(__file__).parent
        self.content_dir = self.root / "content"
        self.templates_dir = self.root / "templates"
        self.output_dir = self.root / "public"
        self.assets_dir = self.root / "assets"
        self.quotes = self.load_quotes()

    def load_quotes(self) -> str:
        """Load quotes from JSON and return as JSON string for template."""
        quotes_file = self.assets_dir / "quotes.json"
        if not quotes_file.exists():
            return "[]"
        
        with open(quotes_file, "r") as f:
            quotes = json.load(f)
        
        # Extract only quote and author fields
        clean_quotes = [
            {"quote": q.get("quote", ""), "author": q.get("author", "")}
            for q in quotes if q.get("quote") and q.get("author")
        ]
        
        return json.dumps(clean_quotes)

    def run(self):
        """Build the entire site."""
        self.clean()
        self.copy_assets()
        self.build_pages()
        self.build_blog()
        self.build_notes()
        self.build_projects()
        print(f"✓ build complete: {self.output_dir}")

    def clean(self):
        """Remove and recreate output directory."""
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "blog").mkdir(exist_ok=True)

    def copy_assets(self):
        """Copy assets, favicon, and robots.txt."""
        shutil.copytree(self.assets_dir, self.output_dir / "assets")
        shutil.copy(self.output_dir / "assets/favicon.ico", self.output_dir / "favicon.ico")
        shutil.copy(self.output_dir / "assets/robots.txt", self.output_dir / "robots.txt")

    def render(self, template_name: str, context: dict) -> str:
        """Render a template with context variables."""
        template_path = self.templates_dir / template_name
        content = template_path.read_text()

        for key, value in context.items():
            if value is not None:
                content = content.replace(f"{{{{{key}}}}}", str(value))

        return content

    def markdown_to_html(self, filepath: Path) -> str:
        """Convert markdown file to HTML."""
        result = subprocess.run(
            ["pandoc", "--from=markdown", "--to=html", str(filepath)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def render_page(self, title: str, content: str, nav_prefix: str) -> str:
        """Render a full page with layout and shared context."""
        return self.render(
            "layout.html",
            {
                "title": title,
                "content": content,
                "nav_prefix": nav_prefix,
                "quotes": self.quotes,
            },
        )

    def file_mtime(self, filepath: Path) -> datetime:
        """Get file modification time."""
        return datetime.fromtimestamp(filepath.stat().st_mtime)

    def date_label(self, dt: datetime) -> str:
        """Format datetime as [YYYY-MM-DD]."""
        return dt.strftime("[%Y-%m-%d]")

    def extract_title(self, filepath: Path) -> str:
        """Extract first h1 from markdown."""
        for line in filepath.read_text().split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    def build_pages(self):
        """Build static pages (home, about)."""
        for name in ["home", "about"]:
            md_file = self.content_dir / f"{name}.md"
            if not md_file.exists():
                continue

            html = self.markdown_to_html(md_file)
            title = self.extract_title(md_file)
            page = self.render_page(title, html, "./")
            output = self.output_dir / f"{name}.html"
            output.write_text(page)

    def build_blog(self):
        """Build blog posts and index."""
        blog_dir = self.content_dir / "blog"
        if not blog_dir.exists():
            return

        posts = []
        for md_file in sorted(blog_dir.glob("*.md")):
            mtime = self.file_mtime(md_file)
            title = self.extract_title(md_file)
            slug = md_file.stem
            posts.append({
                "mtime": mtime,
                "title": title,
                "slug": slug,
                "path": md_file,
            })

        # Build individual posts
        for post in posts:
            html = self.markdown_to_html(post["path"])
            page = self.render_page(post["title"], html, "../")
            (self.output_dir / "blog" / f"{post['slug']}.html").write_text(page)

        # Build blog index
        entries = ""
        for post in sorted(posts, key=lambda p: p["mtime"], reverse=True):
            item = self.render(
                "blog-item.html",
                {
                    "date": self.date_label(post["mtime"]),
                    "title": post["title"],
                    "slug": post["slug"],
                },
            )
            entries += item

        body = self.render("blog.html", {"entries": entries})
        page = self.render_page("Blog", body, "../")
        (self.output_dir / "blog" / "index.html").write_text(page)

    def build_notes(self):
        """Build notes page."""
        notes_dir = self.content_dir / "notes"
        if not notes_dir.exists():
            return

        notes = []
        for note_file in notes_dir.glob("*"):
            if note_file.is_file():
                mtime = self.file_mtime(note_file)
                notes.append({
                    "mtime": mtime,
                    "path": note_file,
                })

        # Build notes page
        entries = ""
        for note in sorted(notes, key=lambda n: n["mtime"], reverse=True):
            html = self.markdown_to_html(note["path"])
            item = self.render(
                "notes-item.html",
                {
                    "date": self.date_label(note["mtime"]),
                    "content": html,
                },
            )
            entries += item

        body = self.render("notes.html", {"entries": entries})
        page = self.render_page("Notes", body, "./")
        (self.output_dir / "notes.html").write_text(page)

    def build_projects(self):
        """Build projects page."""
        projects_file = self.content_dir / "projects.md"
        if not projects_file.exists():
            return

        lines = projects_file.read_text().split("\n")
        entries = ""
        
        for i, line in enumerate(lines):
            if line.strip().startswith("## "):
                header = line.strip()[3:].strip()
                match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', header)
                
                if match:
                    description = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    item = self.render(
                        "projects-item.html",
                        {"title": match.group(1), "description": description, "link": match.group(2)},
                    )
                    entries += item

        body = self.render("projects.html", {"entries": entries})
        page = self.render_page("Projects", body, "./")
        (self.output_dir / "projects.html").write_text(page)


if __name__ == "__main__":
    Builder().run()
