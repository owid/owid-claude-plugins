#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "textual>=0.58.0",
#   "pyyaml>=6.0.1",
# ]
# ///

from __future__ import annotations

import json
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Markdown, Static, Tree


Scope = Literal["user", "project"]


@dataclass
class Skill:
    id: str
    name: str
    plugin_name: str
    source_dir: Path
    markdown_path: Path
    description: str
    target_name: str


@dataclass
class Plugin:
    name: str
    source_dir: Path
    description: str
    skills: list[Skill] = field(default_factory=list)


def git_pull_main(repo_root: Path) -> str:
    if not (repo_root / ".git").exists():
        return "Skipping git pull (not a git repository)."

    cmd = ["git", "-C", str(repo_root), "pull", "--ff-only", "origin", "main"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return f"Updated from origin/main. {output}".strip()
    return f"Git pull failed (continuing anyway): {output}".strip()


def parse_frontmatter_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""

    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except Exception:
        return ""
    return str(frontmatter.get("description", "")).strip()


def load_plugins(repo_root: Path) -> list[Plugin]:
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))

    plugins: list[Plugin] = []
    for p in marketplace.get("plugins", []):
        source_dir = (repo_root / p["source"]).resolve()
        plugin_json = source_dir / ".claude-plugin" / "plugin.json"
        plugin_data = json.loads(plugin_json.read_text(encoding="utf-8"))
        plugins.append(
            Plugin(
                name=plugin_data["name"],
                source_dir=source_dir,
                description=plugin_data.get("description", ""),
            )
        )

    all_skill_names: list[str] = []
    plugin_skill_paths: dict[str, list[Path]] = {}
    for plugin in plugins:
        skills_dir = plugin.source_dir / "skills"
        skill_dirs = sorted([p for p in skills_dir.iterdir() if p.is_dir()]) if skills_dir.exists() else []
        plugin_skill_paths[plugin.name] = skill_dirs
        all_skill_names.extend([sd.name for sd in skill_dirs])

    collisions = Counter(all_skill_names)

    for plugin in plugins:
        for skill_dir in plugin_skill_paths[plugin.name]:
            md_path = skill_dir / "SKILL.md"
            description = parse_frontmatter_description(md_path) if md_path.exists() else ""
            base_name = skill_dir.name
            target_name = base_name if collisions[base_name] == 1 else f"{plugin.name}__{base_name}"
            plugin.skills.append(
                Skill(
                    id=f"{plugin.name}/{base_name}",
                    name=base_name,
                    plugin_name=plugin.name,
                    source_dir=skill_dir,
                    markdown_path=md_path,
                    description=description,
                    target_name=target_name,
                )
            )

    return plugins


class SkillManagerApp(App[None]):
    TITLE = "OWID Skills Installer"
    BINDINGS = [
        Binding("u", "install_user", "Install to ~/.agents/skills"),
        Binding("p", "install_project", "Install to ./.agents/skills"),
        Binding("d", "uninstall", "Uninstall (user+project)"),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    #layout {
        height: 1fr;
    }

    #tree-pane {
        width: 45%;
        border: solid $primary;
    }

    #detail-pane {
        width: 55%;
        border: solid $primary;
    }

    #status {
        height: 3;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(self, repo_root: Path, startup_message: str) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.user_skills_dir = Path.home() / ".agents" / "skills"
        self.project_skills_dir = self.repo_root / ".agents" / "skills"
        self.plugins = load_plugins(repo_root)
        self.skills_by_id: dict[str, Skill] = {
            skill.id: skill for plugin in self.plugins for skill in plugin.skills
        }
        self.startup_message = startup_message
        self.nav_tree: Tree[str] | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="layout"):
            yield Tree("Plugins", id="tree-pane")
            with Vertical(id="detail-pane"):
                yield Markdown("Select a plugin or skill", id="details")
                yield Static(self.startup_message, id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.nav_tree = self.query_one("#tree-pane", Tree)
        root = self.nav_tree.root
        root.expand()

        for plugin in self.plugins:
            p_node = root.add(self._plugin_label(plugin), data=f"plugin:{plugin.name}")
            p_node.expand()
            for skill in plugin.skills:
                p_node.add(self._skill_label(skill), data=f"skill:{skill.id}")

        if root.children:
            self.nav_tree.select_node(root.children[0])
            self._update_details_for_node(root.children[0].data or "")

    def _skill_status(self, skill: Skill) -> str:
        user_installed = self._is_installed(skill, "user")
        project_installed = self._is_installed(skill, "project")
        if user_installed and project_installed:
            return "B"
        if user_installed:
            return "U"
        if project_installed:
            return "P"
        return "·"

    def _plugin_status(self, plugin: Plugin) -> str:
        statuses = {self._skill_status(skill) for skill in plugin.skills}
        if statuses == {"·"}:
            return "·"
        if len(statuses) == 1:
            return next(iter(statuses))
        return "◐"

    def _skill_label(self, skill: Skill) -> str:
        return f"[{self._skill_status(skill)}] {skill.name}"

    def _plugin_label(self, plugin: Plugin) -> str:
        return f"[{self._plugin_status(plugin)}] {plugin.name}"

    def _target_path(self, skill: Skill, scope: Scope) -> Path:
        base = self.user_skills_dir if scope == "user" else self.project_skills_dir
        return base / skill.target_name

    def _is_installed(self, skill: Skill, scope: Scope) -> bool:
        target = self._target_path(skill, scope)
        return target.is_symlink() and target.resolve() == skill.source_dir.resolve()

    def _install_skill(self, skill: Skill, scope: Scope) -> str:
        target = self._target_path(skill, scope)
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() or target.is_symlink():
            if target.is_symlink() and target.resolve() == skill.source_dir.resolve():
                return f"Already installed: {skill.id} -> {scope}"
            return f"Cannot install {skill.id}: target already exists ({target})"

        target.symlink_to(skill.source_dir)
        return f"Installed {skill.id} to {scope}"

    def _uninstall_skill(self, skill: Skill, scope: Scope) -> str:
        target = self._target_path(skill, scope)
        if not target.exists() and not target.is_symlink():
            return f"Not installed in {scope}: {skill.id}"
        if target.is_symlink() and target.resolve() == skill.source_dir.resolve():
            target.unlink()
            return f"Uninstalled {skill.id} from {scope}"
        return f"Skipped {scope} uninstall for {skill.id}: target is not this skill ({target})"

    def _selected_items(self) -> list[Skill]:
        if self.nav_tree is None or self.nav_tree.cursor_node is None:
            return []
        data = self.nav_tree.cursor_node.data or ""
        if data.startswith("skill:"):
            skill_id = data.removeprefix("skill:")
            skill = self.skills_by_id.get(skill_id)
            return [skill] if skill else []
        if data.startswith("plugin:"):
            plugin_name = data.removeprefix("plugin:")
            for plugin in self.plugins:
                if plugin.name == plugin_name:
                    return plugin.skills
        return []

    def _refresh_tree(self) -> None:
        if self.nav_tree is None:
            return
        root = self.nav_tree.root
        for p_node in root.children:
            pdata = p_node.data or ""
            if pdata.startswith("plugin:"):
                plugin_name = pdata.removeprefix("plugin:")
                plugin = next((p for p in self.plugins if p.name == plugin_name), None)
                if plugin:
                    p_node.set_label(self._plugin_label(plugin))
            for s_node in p_node.children:
                sdata = s_node.data or ""
                if sdata.startswith("skill:"):
                    skill_id = sdata.removeprefix("skill:")
                    skill = self.skills_by_id.get(skill_id)
                    if skill:
                        s_node.set_label(self._skill_label(skill))

    def _set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)

    def _update_details_for_node(self, data: str) -> None:
        details = self.query_one("#details", Markdown)
        if data.startswith("plugin:"):
            plugin_name = data.removeprefix("plugin:")
            plugin = next((p for p in self.plugins if p.name == plugin_name), None)
            if not plugin:
                details.update("Plugin not found")
                return
            skill_lines = "\n".join([f"- {s.name} (`{s.target_name}`)" for s in plugin.skills])
            details.update(
                f"# {plugin.name}\n\n"
                f"{plugin.description or 'No description'}\n\n"
                f"## Skills\n{skill_lines or '- (none)'}\n\n"
                f"Press `u` to install selected plugin skills to user scope, `p` for project scope."
            )
            return

        if data.startswith("skill:"):
            skill_id = data.removeprefix("skill:")
            skill = self.skills_by_id.get(skill_id)
            if not skill:
                details.update("Skill not found")
                return
            details.update(
                f"# {skill.name}\n\n"
                f"Plugin: `{skill.plugin_name}`\n\n"
                f"{skill.description or 'No description in SKILL.md frontmatter.'}\n\n"
                f"Source: `{skill.source_dir}`\n\n"
                f"Install name: `{skill.target_name}`\n"
                f"- User: `{self._target_path(skill, 'user')}`\n"
                f"- Project: `{self._target_path(skill, 'project')}`\n\n"
                f"Status: user={self._is_installed(skill, 'user')} project={self._is_installed(skill, 'project')}"
            )
            return

        details.update("Select a plugin or skill")

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        self._update_details_for_node(event.node.data or "")

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted[str]) -> None:
        self._update_details_for_node(event.node.data or "")

    def action_install_user(self) -> None:
        self._install_selected("user")

    def action_install_project(self) -> None:
        self._install_selected("project")

    def _install_selected(self, scope: Scope) -> None:
        skills = self._selected_items()
        if not skills:
            self._set_status("No skill selected.")
            return
        messages = [self._install_skill(skill, scope) for skill in skills]
        self._refresh_tree()
        if self.nav_tree and self.nav_tree.cursor_node:
            self._update_details_for_node(self.nav_tree.cursor_node.data or "")
        self._set_status(" | ".join(messages))

    def action_uninstall(self) -> None:
        skills = self._selected_items()
        if not skills:
            self._set_status("No skill selected.")
            return
        messages: list[str] = []
        for skill in skills:
            messages.append(self._uninstall_skill(skill, "user"))
            messages.append(self._uninstall_skill(skill, "project"))
        self._refresh_tree()
        if self.nav_tree and self.nav_tree.cursor_node:
            self._update_details_for_node(self.nav_tree.cursor_node.data or "")
        self._set_status(" | ".join(messages))


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    # startup_message = git_pull_main(repo_root)
    startup_message = "test"
    app = SkillManagerApp(repo_root=repo_root, startup_message=startup_message)
    app.run()


if __name__ == "__main__":
    main()
