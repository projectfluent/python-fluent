import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from .tags import get_tag_infos


def build(repo_name, projects, releases_after=None):
    """Build documentation for projects.

    Build the given projects in _build/repo_name.
    Create versioned documentations for tags after ``releases_after``,
    if given.
    """
    tagged_versions = []
    if releases_after:
        tagged_versions = [
            tag for tag in get_tag_infos(releases_after) if tag.project in projects
        ]
    # List of versions we have for each project
    versions_4_project = defaultdict(list)
    for tag in tagged_versions:
        versions_4_project[tag.project].append(tag.version)
    last_vers = {}
    for project in projects:
        if project in versions_4_project:
            last_vers[project] = versions_4_project[project][0]
            versions_4_project[project][:0] = ["dev", "stable"]
        else:
            # No releases yet, just dev
            last_vers[project] = "dev"
            versions_4_project[project].append("dev")
    # Build current dev version for each project
    for project in projects:
        src_dir = project
        builder = ProjectBuilder(
            repo_name, src_dir, project, versions_4_project[project], "dev"
        )
        with builder:
            builder.build()
        # Create redirect page from project to stable release or dev
        index = Path(f"_build/{repo_name}/{project}/index.html")
        target = "stable" if last_vers[project] != "dev" else "dev"
        index.write_text(f'<meta http-equiv="refresh" content="0; URL={target}/">\n')
    worktree = None
    for tag in tagged_versions:
        if worktree is None:
            worktree = tempfile.mkdtemp()
            subprocess.run(["git", "worktree", "add", "--detach", worktree])
        subprocess.run(
            ["git", "checkout", f"{tag.project}@{tag.version}"], cwd=worktree
        )
        with ProjectBuilder(
            repo_name,
            os.path.join(worktree, tag.project),
            tag.project,
            versions_4_project[tag.project],
            tag.version,
        ) as builder:
            builder.build()
    if worktree is not None:
        shutil.rmtree(worktree)
    for project in projects:
        if last_vers[project] == "dev":
            continue
        stable = Path(f"_build/{repo_name}/{project}/stable")
        if stable.is_symlink():
            stable.unlink()
        if stable.exists():
            shutil.rmtree(stable)
        stable.symlink_to(last_vers[project], target_is_directory=True)


class DocBuilder:
    """Builder for the top-level documentation."""

    def __init__(self, repo_name, src_dir):
        self.repo_name = repo_name
        self.src_dir = src_dir

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def build(self):
        cmd = self.command()
        env = self.environ()
        subprocess.check_call(cmd, env=env)

    def command(self):
        return (
            self.cmd_prefix
            + self.cmd_opts
            + [
                f"{self.src_dir}/docs",
                self.dest_dir,
            ]
        )

    def environ(self):
        return os.environ.copy()

    @property
    def cmd_prefix(self):
        return [
            "sphinx-build",
            "-c",
            "docs",
            "-a",
            "-E",
            "-W",
            "-A",
            "root_url=/" + self.repo_name,
            "-d",
            self.doc_tree,
        ]

    @property
    def cmd_opts(self):
        return []

    @property
    def dest_dir(self):
        return f"_build/{self.repo_name}"

    @property
    def doc_tree(self):
        return "_build/doctrees"


class ProjectBuilder(DocBuilder):
    """Builder for individual projects, with project name and version."""

    def __init__(self, repo_name, src_dir, project_name, versions, version):
        super().__init__(repo_name, src_dir)
        self.project_name = project_name
        self.versions = versions
        self.version = version

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove static theme files from project static, they're
        # used from the top-level _static.
        for staticfile in Path(self.dest_dir).glob("_static/*"):
            # The options are project-specific.
            if staticfile.name != "documentation_options.js":
                staticfile.unlink()
        return False

    def build(self):
        self.create_versions_doc()
        super().build()

    def environ(self):
        env = super().environ()
        env["PYTHONPATH"] = self.src_dir
        return env

    @property
    def cmd_opts(self):
        opts = [
            "-D",
            "project=" + self.project_name,
        ]
        if self.version != "dev":
            opts += [
                "-D",
                f"release={self.version}",
            ]
        return opts

    @property
    def dest_dir(self):
        return f"_build/{self.repo_name}/{self.project_name}/{self.version}"

    def create_versions_doc(self):
        target_path = Path(self.src_dir) / "docs" / "_templates"
        target_path.mkdir(exist_ok=True)
        target_path = target_path / "versions.html"
        links = " ".join(
            f'<a href="/{self.repo_name}/{self.project_name}/{v}">{v}</a>'
            for v in self.versions
        )
        content = f"""<h3>Versions</h3>
<p id="versions">
    <span class="version">{self.version}</span>
    <span class="links">{links}</span>
</p>
"""
        target_path.write_text(content)
