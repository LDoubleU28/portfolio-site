# tests/test_tier.py
from build_lib import load_recognition

def test_public_tier_has_no_names(tmp_path):
    pub = tmp_path / "recognition.yaml"
    pub.write_text("- id: q1\n  text: 'Great work'\n  broadened_role: 'a leader'\n")
    internal_dir = tmp_path / "content_internal"
    internal_dir.mkdir()
    (internal_dir / "names_map.yaml").write_text("q1: {name: 'Real Name', role: 'VP', slack_link: 'https://x'}\n")

    recs = load_recognition(str(pub), str(internal_dir), tier="public")
    assert recs[0]["text"] == "Great work"
    assert recs[0]["attribution"] == "a leader"
    assert "name" not in recs[0]
    assert "slack_link" not in recs[0]

def test_internal_tier_has_names(tmp_path):
    pub = tmp_path / "recognition.yaml"
    pub.write_text("- id: q1\n  text: 'Great work'\n  broadened_role: 'a leader'\n")
    internal_dir = tmp_path / "content_internal"
    internal_dir.mkdir()
    (internal_dir / "names_map.yaml").write_text("q1: {name: 'Real Name', role: 'VP', slack_link: 'https://x'}\n")

    recs = load_recognition(str(pub), str(internal_dir), tier="internal")
    assert recs[0]["name"] == "Real Name"
    assert recs[0]["attribution"] == "Real Name, VP"
    assert recs[0]["slack_link"] == "https://x"

def test_public_tier_never_reads_internal_dir(tmp_path):
    pub = tmp_path / "recognition.yaml"
    pub.write_text("- id: q1\n  text: 'Great work'\n  broadened_role: 'a leader'\n")
    # internal dir does NOT exist; public must not require it
    recs = load_recognition(str(pub), str(tmp_path / "missing"), tier="public")
    assert recs[0]["attribution"] == "a leader"
