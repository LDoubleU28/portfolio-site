# build.py
import argparse
from build_lib import render_site

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default="neutral")
    ap.add_argument("--tier", choices=["public", "internal"], default="public")
    ap.add_argument("--out", default=None)
    ap.add_argument("--content", default="content")
    ap.add_argument("--internal", default="content_internal")
    ap.add_argument("--templates", default="templates")
    a = ap.parse_args()
    out = a.out or f"build/{a.theme}"
    render_site(a.content, a.internal, a.templates, a.theme, a.tier, out)
    print(f"Built {a.theme}/{a.tier} -> {out}")

if __name__ == "__main__":
    main()
