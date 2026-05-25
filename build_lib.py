# build_lib.py
import hashlib
import os
import yaml

def _load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def _load_yaml_opt(path):
    """Load a YAML file if it exists, else return None (for optional content)."""
    return _load_yaml(path) if os.path.exists(path) else None

def load_recognition(public_path, internal_dir, tier="public"):
    recs = _load_yaml(public_path) or []
    out = []
    names = {}
    if tier == "internal":
        names_path = os.path.join(internal_dir, "names_map.yaml")
        if os.path.exists(names_path):
            names = _load_yaml(names_path) or {}
    for r in recs:
        item = {"id": r["id"], "text": r["text"]}
        if tier == "internal" and r["id"] in names:
            n = names[r["id"]]
            item["name"] = n["name"]
            item["role"] = n.get("role", "")
            item["slack_link"] = n.get("slack_link", "")
            item["attribution"] = f'{n["name"]}, {n["role"]}' if n.get("role") else n["name"]
        else:
            item["attribution"] = r["broadened_role"]
        out.append(item)
    return out

# append to build_lib.py
from jinja2 import Environment, FileSystemLoader
import shutil

def _asset_version(out_dir):
    """Content hash of the versioned static assets (the CSS/JS referenced with
    ?v=). Stable across deploys when the files are unchanged, so browsers and
    CDNs reuse cached copies instead of re-fetching on every build."""
    targets = [
        os.path.join(out_dir, "themes", "tokens.css"),
        os.path.join(out_dir, "assets", "js", "chat.js"),
    ]
    # Include any theme stylesheets so a theme edit busts the cache.
    themes_dir = os.path.join(out_dir, "themes")
    if os.path.isdir(themes_dir):
        for fn in sorted(os.listdir(themes_dir)):
            if fn.endswith(".css"):
                targets.append(os.path.join(themes_dir, fn))
    h = hashlib.sha256()
    for p in sorted(set(targets)):
        if os.path.isfile(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:12]

def load_all(content_dir, internal_dir, tier):
    return {
        "profile": _load_yaml(os.path.join(content_dir, "profile.yaml")),
        "projects": _load_yaml(os.path.join(content_dir, "projects.yaml")),
        "leadership": _load_yaml(os.path.join(content_dir, "leadership.yaml")),
        "recognition": load_recognition(
            os.path.join(content_dir, "recognition.yaml"), internal_dir, tier),
        "experience": _load_yaml_opt(os.path.join(content_dir, "experience.yaml")),
        "about": _load_yaml_opt(os.path.join(content_dir, "about.yaml")),
        "case_brain": _load_yaml_opt(os.path.join(content_dir, "case_brain.yaml")),
        "tier": tier,
    }

def render_site(content_dir, internal_dir, templates_dir, theme, tier, out_dir):
    data = load_all(content_dir, internal_dir, tier)
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    shutil.rmtree(out_dir, ignore_errors=True)  # clean build: no stale assets
    os.makedirs(out_dir, exist_ok=True)
    # copy static asset dirs
    for d in ("themes", "assets"):
        if os.path.isdir(d):
            shutil.copytree(d, os.path.join(out_dir, d), dirs_exist_ok=True)
    # internal screenshots only for internal tier
    if tier == "internal":
        shots = os.path.join(internal_dir, "screenshots")
        if os.path.isdir(shots):
            shutil.copytree(shots, os.path.join(out_dir, "assets", "img", "screenshots"), dirs_exist_ok=True)
    # Pages: home always; experience/about only when their content exists.
    pages = [("home.html.j2", "index.html", "Work")]
    pages.append(("leadership.html.j2", "leadership.html", "Leadership"))
    if data.get("experience"):
        pages.append(("experience.html.j2", "experience.html", "Experience"))
    if data.get("about"):
        pages.append(("about.html.j2", "about.html", "About"))
    if data.get("case_brain"):
        pages.append(("case-brain.html.j2", "brain.html", "The Brain"))
    # Cache-bust on content, not wall-clock time, so unchanged assets keep a
    # stable URL and are not re-downloaded on every deploy.
    asset_version = _asset_version(out_dir)
    for template_name, out_name, page_title in pages:
        tmpl = env.get_template(template_name)
        html = tmpl.render(theme=theme, page_title=page_title, asset_version=asset_version, **data)
        with open(os.path.join(out_dir, out_name), "w") as f:
            f.write(html)
    return out_dir
