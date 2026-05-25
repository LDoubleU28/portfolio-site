# tests/test_leak_gate.py
from checks.leak_gate import scan_dir, load_denylist

def test_flags_real_name(tmp_path):
    (tmp_path / "page.html").write_text("<p>Quote by Real Person</p>")
    violations = scan_dir(str(tmp_path), names=["Real Person"])
    assert any("Real Person" in v.detail for v in violations)

def test_flags_slack_link(tmp_path):
    (tmp_path / "p.html").write_text('<a href="https://oplabs.slack.com/archives/x">link</a>')
    violations = scan_dir(str(tmp_path), names=[])
    assert any("slack.com" in v.detail for v in violations)

def test_flags_slack_workspace_root_link(tmp_path):
    # No trailing path, no trailing slash -- must still be caught.
    (tmp_path / "p.html").write_text('<a href="https://oplabs.slack.com">link</a>')
    violations = scan_dir(str(tmp_path), names=[])
    assert any("slack.com" in v.detail for v in violations)

def test_flags_slack_deeplink(tmp_path):
    (tmp_path / "p.html").write_text('<a href="slack://channel?team=T1&id=C1">open</a>')
    violations = scan_dir(str(tmp_path), names=[])
    assert any("slack" in v.detail.lower() for v in violations)

def test_committed_denylist_loads_and_is_nonempty():
    # The committed denylist must load unconditionally (independent of any
    # git-ignored content_internal/ dir).
    terms = load_denylist()
    assert isinstance(terms, list)
    assert len(terms) > 0

def test_denylist_enforced_with_no_names_map(tmp_path):
    # NEGATIVE TEST: with names=[] (no internal names map present, as on the
    # public deploy), a built page containing a committed denylist token must
    # still be flagged purely from checks/denylist.txt.
    terms = load_denylist()
    assert terms, "denylist must be seeded for this test to be meaningful"
    token = terms[0]
    (tmp_path / "page.html").write_text(f"<p>contact {token} for details</p>")
    violations = scan_dir(str(tmp_path), names=[])
    assert any(token.lower() in v.detail.lower() for v in violations), (
        "gate failed to flag a committed-denylist token when no names map is present"
    )

def test_flags_screenshot_reference(tmp_path):
    (tmp_path / "p.html").write_text('<img src="screenshots/feedback1.png">')
    violations = scan_dir(str(tmp_path), names=[])
    assert any("screenshots/" in v.detail for v in violations)

def test_clean_build_passes(tmp_path):
    (tmp_path / "p.html").write_text("<p>a senior program leader said it was useful</p>")
    violations = scan_dir(str(tmp_path), names=["Real Person"])
    assert violations == []
