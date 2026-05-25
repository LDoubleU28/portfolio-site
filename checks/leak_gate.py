# checks/leak_gate.py
"""Scan built site dirs (and the shipped chatbot knowledge bundle) for
internal-tier leakage. Exit nonzero if any found.

Two name sources are enforced:
  1. checks/denylist.txt -- committed, loaded UNCONDITIONALLY, so the gate
     catches forbidden terms on the public deploy even though content_internal/
     is git-ignored.
  2. content_internal/names_map.yaml -- optional, only present in private
     builds; merged on top of the committed denylist when available.
"""
import os, sys, re
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
DENYLIST_PATH = os.path.join(HERE, "denylist.txt")

FORBIDDEN_PATTERNS = [
    # Slack links: https/http web links to any *.slack.com (root or with a path),
    # and the slack:// deep-link scheme.
    (re.compile(r"https?://[a-z0-9.-]*slack\.com\b", re.I), "slack.com link"),
    (re.compile(r"slack://", re.I), "slack:// link"),
    (re.compile(r"screenshots/"), "screenshots/ reference"),
]

SCAN_EXTS = (".html", ".js", ".mjs", ".css", ".json")

@dataclass
class Violation:
    path: str
    detail: str

def _name_regex(name):
    # Case-insensitive, word-boundary match. \b is unreliable when a term ends
    # in a non-word char, so anchor on (?<!\w) ... (?!\w) lookarounds.
    return re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.I)

def load_denylist(path=DENYLIST_PATH):
    """Load committed denylist terms. Always available; returns [] if missing."""
    if not os.path.exists(path):
        return []
    terms = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            terms.append(line)
    return terms

def _scan_text(text, name_res):
    found = []
    for pat, label in FORBIDDEN_PATTERNS:
        if pat.search(text):
            found.append(label)
    for name, nre in name_res:
        if nre.search(text):
            found.append(f"real name: {name}")
    return found

def scan_dir(build_dir, names):
    """Scan every shippable file under build_dir.

    The committed denylist is ALWAYS enforced, merged with any `names` passed
    in (e.g. from content_internal/names_map.yaml).
    """
    violations = []
    all_names = list(dict.fromkeys([n for n in (list(names) + load_denylist()) if n]))
    name_res = [(n, _name_regex(n)) for n in all_names]
    for root, _, files in os.walk(build_dir):
        for fn in files:
            if not fn.endswith(SCAN_EXTS):
                continue
            fp = os.path.join(root, fn)
            with open(fp, errors="ignore") as f:
                text = f.read()
            for label in _scan_text(text, name_res):
                violations.append(Violation(fp, label))
    return violations

def scan_file(path, names):
    """Scan a single file (used for the shipped chatbot knowledge bundle)."""
    if not os.path.exists(path):
        return []
    all_names = list(dict.fromkeys([n for n in (list(names) + load_denylist()) if n]))
    name_res = [(n, _name_regex(n)) for n in all_names]
    with open(path, errors="ignore") as f:
        text = f.read()
    return [Violation(path, label) for label in _scan_text(text, name_res)]

def _load_names(internal_dir):
    import yaml
    p = os.path.join(internal_dir, "names_map.yaml")
    if not os.path.exists(p):
        return []
    data = yaml.safe_load(open(p)) or {}
    return [v["name"] for v in data.values() if isinstance(v, dict) and v.get("name")]

if __name__ == "__main__":
    build_dir = sys.argv[1]
    internal_dir = sys.argv[2] if len(sys.argv) > 2 else "content_internal"
    names = _load_names(internal_dir)
    violations = scan_dir(build_dir, names)
    # Also scan the chatbot knowledge bundle that actually ships, even though it
    # lives outside the published build dir.
    kb_targets = ["netlify/functions/lib/knowledge.mjs", "netlify/functions"]
    kb_path = next((p for p in kb_targets if os.path.exists(p)), None)
    if kb_path:
        if os.path.isdir(kb_path):
            for root, _, files in os.walk(kb_path):
                for fn in files:
                    if fn.endswith(SCAN_EXTS):
                        violations.extend(scan_file(os.path.join(root, fn), names))
        else:
            violations.extend(scan_file(kb_path, names))
    if violations:
        print(f"LEAK-GATE FAILED: {len(violations)} violation(s) in {build_dir} (+ chatbot bundle)")
        for x in violations:
            print(f"  {x.path}: {x.detail}")
        sys.exit(1)
    print(f"LEAK-GATE PASSED: {build_dir} clean (build + chatbot knowledge bundle)")
