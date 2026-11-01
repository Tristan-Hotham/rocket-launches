"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/launches.json and
data/reentries.json are loaded by the page. Facts stated in words are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23857612 and https://blog.tristanhotham.com/2026/10/31/rocket-launches/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
PK, PT, B, G = R["peaks"], R["ports"], R["blocs"], {g["name"]: g for g in R["stations"]}

# facts stated in words (page, blog, paper, collage)
assert R["sputnik"]["n1957"] == 3 and R["sputnik"]["fail1957"] == 1
assert PK["coldwar_year"] == 1967 and PK["us_1960s_year"] == 1966 and PK["su_year"] == 1982 and PK["dip_year"] == 2004 and PK["record_year"] == 2025
assert 1970 <= R["plesetsk"]["peak_year"] <= 1989
assert PK["spx_2025_pct"] > 50 and PK["f9_2025"] > 120          # "more than half", "every two or three days"
assert 2000 <= PK["dip_year"] <= 2005 and PK["dip_n"] < 60         # "little more than one a week" in the early 2000s
assert B["China"]["since2020"] > B["Soviet Union and Russia"]["since2020"]
assert 20 < R["fail"]["first10_pct"] < 25                           # "almost one in four"
assert R["fail"]["max_year"] == 1958
assert sorted(b["bloc"] for b in R["blocs_list"] if b["fail_pct"] > 20) == ["Others"]
assert R["busiest_ever"][0]["port"] == "Plesetsk" and R["busiest_ever"][1]["port"] == "Baikonur"
assert PT["Mahia"]["y2025"] > PT["Baikonur"]["y2025"] and PT["Mahia"]["first"] == 2017
assert R["busiest_2025"][0]["port"] == "Cape Canaveral and Kennedy" and R["busiest_2025"][1]["port"] == "Vandenberg"
assert {r["port"] for r in R["busiest_2020s"][:7]} >= {"Jiuquan", "Xichang", "Taiyuan", "Wenchang"}
assert R["lat"]["kourou_gto_pct"] > R["lat"]["cape_gto_pct"] > R["lat"]["baikonur_gto_pct"] > 5 > R["lat"]["plesetsk_gto_pct"]
assert R["dir"]["palmachim_retro"] == 100 and R["dir"]["vandenberg_polar"] > 60 and R["dir"]["cape_east"] > 95
assert G["Skylab"]["status"] == "R" and -35 < G["Skylab"]["lat"] < -14 and 115 < G["Skylab"]["lon"] < 129      # Western Australia
assert G["Salyut 2"]["status"] == "R" and G["Salyut 7"]["status"] == "R" and G["Tiangong 2"]["status"] == "D" and G["Tiangong 2"]["lat"] < -20
assert -25 < G["Tiangong 1"]["lat"] < 0 and -180 < G["Tiangong 1"]["lon"] < -140                                 # central South Pacific
assert R["located"]["unc_sea_pct"] > 70 and R["located"]["unc_near_nemo_pct"] < 10
assert R["objects"]["deorbited_pct_of_down"] < 1 and abs(R["objects"]["came_down_pct"] - 50) < 1             # "about half"
assert R["before"]["v2_first"] == 1942 and R["before"]["first_space_date"] == "1944 Jun"
assert R["source"]["last_date"].startswith("2026")


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23857612", "https://blog.tristanhotham.com/2026/10/31/rocket-launches/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
