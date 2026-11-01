"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23857612, https://doi.org/10.5281/zenodo.23857612 and https://blog.tristanhotham.com/2026/10/31/rocket-launches/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Up_and_Down"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
pk, PT = R["peaks"], R["ports"]
assert [PT[p]["n"] for p in ("Plesetsk", "Baikonur", "Cape Canaveral and Kennedy", "Vandenberg", "Kourou")] == [1686, 1558, 1393, 938, 336]
assert [r["n"] for r in R["busiest_2025"][:6]] == [109, 66, 33, 21, 19, 17] and R["busiest_2025"][5]["port"] == "Mahia"
assert (pk["coldwar_n"], pk["dip_n"], pk["record_n"]) == (139, 54, 329)
assert R["blocs"]["China"]["first"] == 1970 and pk["f9_2025"] * 2 > pk["record_n"]                       # "more than half of them SpaceX Falcon 9s"
assert pk["first_over_coldwar"] - pk["coldwar_year"] == 54
assert R["lat"]["kourou_v"] == 463 and R["lat"]["plesetsk_v"] == 212
D = {d["dec"]: d["fail_pct"] for d in R["decades"]}
assert round(D[1950]) == 57 and round(D[1960]) == 16
Y = {y["y"]: y for y in R["years"]}
assert max(Y[y]["fail"] for y in range(1958, 1970)) == 20 and all(Y[y]["fail"] <= 11 for y in range(2020, 2027))
assert sum(Y[y]["fail"] > 8 for y in range(1975, 2020)) == 1                                             # "mostly between 1 and 8"
DY = {d["y"]: d for d in R["down_years"]}
assert all(1800 < DY[y]["n"] < 2300 for y in (2023, 2024, 2025))                                         # "around 2,000 a year since"
assert R["asat"]["y2022"] / DY[2022]["n"] > .5                                                            # "mostly debris"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23857612"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Up and down: every rocket launch since Sputnik, and where it all comes back",
        "slug": "rocket-launches",
        "excerpt": f"I mapped all {s['n']:,} orbital launch attempts since Sputnik from Jonathan McDowell's catalogue. The world launched a record {pk['record_n']} in {pk['record_year']}, more than half by SpaceX, and half of everything ever catalogued has already fallen back.",
        "seo_description": f"A map of {s['n']:,} orbital launches since 1957: the space race, the record {pk['record_n']} of {pk['record_year']}, the busiest spaceports and the Point Nemo graveyard.",
        "tags": ["spaceflight", "rockets", "maps", "data visualisation", "space debris", "Point Nemo", "SpaceX", "GCAT"],
        "header_alt": f"Title card reading 'Up and down' in red, black and blue on pale paper, beside a world map with circles for spaceports, big red ones at Plesetsk and Baikonur and blue ones in Florida and California, a dashed circle around Point Nemo in the South Pacific, and below it a stacked area chart of launches per year rising to {pk['record_n']} in {pk['record_year']}. Text: every orbital launch since Sputnik, {s['n']:,} attempts."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/rocket-launches_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"rocket-launches/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"rocket-launches/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "rocket-launches/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Up and Down: Seventy Years of Orbital Launches and Where Space Hardware Comes Back to Earth",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Launch and object data: GCAT (J. McDowell, planet4589.org/space/gcat), CC BY 4.0.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["spaceflight", "orbital launches", "spaceports", "launch failures", "space debris", "atmospheric re-entry", "Point Nemo", "GCAT", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": GCAT_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
