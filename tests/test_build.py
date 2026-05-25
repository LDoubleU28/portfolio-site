# tests/test_build.py
import os
from build_lib import render_site

def _fixture(tmp_path, internal_names=None):
    c = tmp_path / "content"; c.mkdir()
    (c / "profile.yaml").write_text(
        "name: Lizzy Wong\nnav: [{label: Work, href: '/#work'}]\nhero_headline_pre: 'I build '\n"
        "hero_headline_accent: 'systems'\nhero_headline_post: ' that run them.'\n"
        "hero_paragraphs: ['p one']\nstack_line: 'Python'\n"
        "stats: [{n: '3', k: 'systems'}]\ntrack_line: 'prev'\npositioning: 'pos'\n"
        "links: [{label: LinkedIn, url: 'https://x'}]\n")
    (c / "projects.yaml").write_text(
        "- {id: brain, featured: true, name: The Brain, type: OS, one_line: ol, "
        "arc: {Problem: pr, Built: bu, 'In use': iu, Measured: me}, "
        "media: {type: slot, label: demo}}\n"
        "- {id: claire, name: Claire, type: NL, one_line: ol2, result: 76 tables}\n")
    (c / "leadership.yaml").write_text(
        "lede: ld\npillars: [{title: t1, body: b1}]\nclosing: cl\n"
        "operating_rigor: {lede: orl, items: [{h: h1, p: p1}]}\n")
    (c / "recognition.yaml").write_text("- {id: q1, text: 'Great', broadened_role: 'a leader'}\n")
    idir = tmp_path / "content_internal"; idir.mkdir()
    if internal_names:
        (idir / "names_map.yaml").write_text("q1: {name: 'Real Person', role: 'VP', slack_link: 'https://oplabs.slack.com/x'}\n")
    return str(c), str(idir)

def test_public_build_has_quote_text_not_name(tmp_path):
    c, i = _fixture(tmp_path, internal_names=True)
    out = render_site(c, i, "templates", "neutral", "public", str(tmp_path / "out"))
    html = open(os.path.join(out, "index.html")).read()  # recognition lives on the home page
    assert "Great" in html
    assert "a leader" in html
    assert "Real Person" not in html        # name must NOT leak into public build
    assert "slack.com" not in html

def test_internal_build_has_name(tmp_path):
    c, i = _fixture(tmp_path, internal_names=True)
    out = render_site(c, i, "templates", "neutral", "internal", str(tmp_path / "outi"))
    html = open(os.path.join(out, "index.html")).read()  # recognition lives on the home page
    assert "Real Person" in html

def test_hero_accent_rendered(tmp_path):
    c, i = _fixture(tmp_path)
    out = render_site(c, i, "templates", "neutral", "public", str(tmp_path / "o2"))
    html = open(os.path.join(out, "index.html")).read()
    assert '<span class="accent">systems</span>' in html
