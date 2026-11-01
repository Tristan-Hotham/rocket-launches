"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23857612 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Up_and_Down"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert 4 <= min(d["fail_pct"] for d in R["decades"][3:]) and max(d["fail_pct"] for d in R["decades"][3:]) <= 6.5   # "between about 4% and 6%"
assert R["fail"]["y2025"] >= max(y["fail"] for y in R["years"] if 1975 <= y["y"] <= 2019)                        # "higher than at any time since the early 1970s"
assert R["ports"]["Baikonur"]["since2020"] == R["busiest_2020s"][7]["n"]                                           # "Baikonur eighth"
assert R["peaks"]["record_n"] >= 2 * R["peaks"]["coldwar_n"] * .99 or R["peaks"]["record_vs_coldwar_pct"] > 100    # "already doubled"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(b['bloc'])} & {b['n']:,} & {b['pct']:.1f}\\% & {b['fail']:,} & {b['fail_pct']:.1f}\\% & {b['first']} & {b['peak_year']} ({b['peak_n']}) & {b['since2020']:,}\\\\\n" for b in R["blocs_list"])
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Orbital launch attempts by launching country or bloc (state of the first agency in GCAT).}\\label{tab:blocs}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Bloc & Attempts & Share & Failed & Rate & First & Peak year & Since 2020\\\\\\midrule\n" + rows +
      f"\\midrule All & {R['source']['n']:,} & 100\\% & {R['source']['fail']:,} & {R['source']['fail_pct']:.1f}\\% & 1957 & {R['peaks']['record_year']} ({R['peaks']['record_n']}) & {R['peaks']['since2020']:,}\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
P = sorted(R["ports"].values(), key=lambda p: -p["n"])[:20]
rows = "".join(f"{tex(p['port'])} & {tex(p['host'])} & {p['lat']:.1f} & {p['n']:,} & {p['fail']} & {p['first']} & {p['peak_year']} ({p['peak_n']}) & {p['since2020']} & {p['y2025']}\\\\\n" for p in P)
TP = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The twenty busiest spaceports: latitude, attempts, failures, first year, busiest year, attempts since 2020 and in 2025.}\\label{tab:ports}"
      "\\begin{tabular}{llrrrrrrr}\\toprule Spaceport & Country & Lat. & Attempts & Failed & First & Busiest & 2020+ & 2025\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(g['name'])} & {g['launched']} & {tex(g['down'])} & {g['mass_t']:.1f} & {'deorbited' if g['status'] == 'D' else 're-entered'} & {tex(g['dest'])}\\\\\n" for g in R["stations"])
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Space stations in GCAT: launch year, end date, mass (main module), status and recorded place.}\\label{tab:stations}"
      "\\begin{tabular}{lrrrll}\\toprule Station & Launched & Came down & Tonnes & Status & GCAT place\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("BLOCS", TB), ("PORTS", TP), ("STATIONS", TS)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
