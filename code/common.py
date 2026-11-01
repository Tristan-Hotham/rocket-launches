"""Shared paths, groupings and helpers for the rocket-launches project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw8/launches/gcat_launch.tsv   GCAT launch list (all launches, orbital and suborbital)
  /home/claude/newdata/raw8/launches/gcat_sites.tsv    GCAT launch sites (codes, names, longitude, latitude)
  /home/claude/newdata/raw8/launches/gcat_orgs.tsv     GCAT organisations (agency codes to state codes)
  /home/claude/newdata/raw8/launches/gcat_lv.tsv       GCAT launch vehicles (used only for family names)
  /home/claude/newdata/raw8/launches/gcat_satcat.tsv   GCAT main object catalogue (satcat): every catalogued object,
                                                       its type, status (in orbit, re-entered, deorbited, landed...)
                                                       and decay date
  /home/claude/newdata/raw8/launches/gcat_index.html   GCAT documentation index and citation/licence notice
      All GCAT files: Jonathan C. McDowell, General Catalog of Artificial Space Objects, Release 1.8.8,
      https://planet4589.org/space/gcat (data update 29 October 2026). CC BY 4.0.
  /home/claude/newdata/raw8/launches/wiki_Point_Nemo.json, wiki_Spacecraft_cemetery.json, wiki_Spaceport.json,
  wiki_List_of_rocket_launch_sites.json
      English Wikipedia articles (HTML, revision ids inside), CC BY-SA 4.0. Used only for facts quoted in the text
      (Point Nemo's position; what the spacecraft cemetery is and which craft have been put there).
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("RL_RAW", "/home/claude/newdata/raw8/launches")
GEO = os.environ.get("RL_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("RL_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("RLTMP", "/dev/shm/rocketlaunches"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "rocket-launches"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23857612"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/rocket-launches/"          # filled in by the publisher
GCAT_URL = "https://planet4589.org/space/gcat"
GCAT_REL = "1.8.8"
GCAT_UPDATE = "2026"           # data update (year only in public copy)
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
LAST_YEAR = 2026               # the catalogue runs to late October 2026: the last year is partial

# Point Nemo, the oceanic pole of inaccessibility (Wikipedia, "Pole of inaccessibility": 48 52.6 S, 123 23.6 W)
NEMO = (-48.8767, -123.3933)
NEMO_R_KM = 2500               # radius of the indicative graveyard circle drawn on the maps (my choice, see paper)

# Launching country or bloc, from the launch agency's state code in GCAT (orgs.tsv). Order = legend and stack order.
BLOCS = [("United States", "#2F5FA7"), ("Soviet Union and Russia", "#C8322B"), ("China", "#E0A11B"),
         ("Europe", "#2E9A8C"), ("Japan", "#D46A8C"), ("India", "#7B57A8"), ("New Zealand (Rocket Lab)", "#3B3B3B"),
         ("Others", "#A79F94")]
STATE_BLOC = {"US": "United States", "SU": "Soviet Union and Russia", "RU": "Soviet Union and Russia", "CN": "China",
              "F": "Europe", "I-ESA": "Europe", "I-ELDO": "Europe", "I": "Europe", "D": "Europe", "UK": "Europe",
              "J": "Japan", "IN": "India", "NZ": "New Zealand (Rocket Lab)"}
AGENCY_STATE_FIX = {"KVR": "RU"}   # Russian Space Forces: agency code missing from orgs.tsv

# GCAT site codes grouped into spaceports. Name, present-day host country, and the codes that make it up.
# Codes come from sites.tsv; where a site was renamed or split (e.g. NIIP-5 then GIK-5 at Baikonur) the codes are merged.
SPACEPORTS = [
    ("Baikonur", "Kazakhstan", ["NIIP-5", "GIK-5"]),
    ("Plesetsk", "Russia", ["NIIP-53", "GIK-1", "GNIIPV", "GNIIP"]),
    ("Cape Canaveral and Kennedy", "United States", ["CC", "KSC", "SPFL", "SPFLA"]),
    ("Vandenberg", "United States", ["V", "VS", "VSFB", "VSFBS", "PA"]),
    ("Kourou", "French Guiana", ["CSG"]),
    ("Jiuquan", "China", ["JQ"]),
    ("Xichang", "China", ["XSC"]),
    ("Taiyuan", "China", ["TYSC", "TYSC?"]),
    ("Sriharikota", "India", ["SHAR", "SDSC"]),
    ("Tanegashima", "Japan", ["TNSC"]),
    ("Kapustin Yar", "Russia", ["GTsP-4", "GTsMP-4"]),
    ("Mahia", "New Zealand", ["MAHIA"]),
    ("Wenchang", "China", ["WEN", "HCSLS"]),
    ("Wallops", "United States", ["WI", "MARS", "WIMB"]),
    ("Uchinoura", "Japan", ["KASC", "USC"]),
    ("Sea Launch, Pacific", "International waters", ["KLA"]),
    ("Vostochny", "Russia", ["VOST"]),
    ("Svobodny", "Russia", ["GIK-2"]),
    ("Yellow Sea launches", "International waters", ["HHAI"]),
    ("Yangjiang sea launches", "International waters", ["YJ"]),
    ("East China Sea launches", "International waters", ["ECS"]),
    ("Semnan", "Iran", ["SEM"]),
    ("Shahroud", "Iran", ["SHAHR"]),
    ("Palmachim", "Israel", ["PALB"]),
    ("Starbase", "United States", ["STB"]),
    ("Kwajalein", "Marshall Islands", ["KMR"]),
    ("Yasny", "Russia", ["YAS"]),
    ("San Marco, Kenya", "Kenya", ["SMLC"]),
    ("Naro", "South Korea", ["NARO"]),
    ("Jeju sea launch", "South Korea", ["JEJU"]),
    ("Sohae", "North Korea", ["SOHAE"]),
    ("Tonghae", "North Korea", ["TONGH"]),
    ("Woomera", "Australia", ["WOO"]),
    ("Kodiak", "United States", ["KLC", "PSCA"]),
    ("China Lake (air launch)", "United States", ["NOTS"]),
    ("Edwards (air launch)", "United States", ["EAFB"]),
    ("Mojave (air launch)", "United States", ["MHV"]),
    ("Hammaguir", "Algeria", ["HMG"]),
    ("Alcantara", "Brazil", ["ALCA"]),
    ("Barents Sea (submarine)", "International waters", ["BLA"]),
    ("Spaceport Kii", "Japan", ["KII"]),
    ("Andoya", "Norway", ["AND"]),
    ("Newquay (air launch)", "United Kingdom", ["NEWQ"]),
    ("Gran Canaria (air launch)", "Spain", ["GANC"]),
    ("Kauai", "United States", ["KAU"]),
    ("Bowen", "Australia", ["BOWEN"]),
]
SITE_PORT = {c: n for n, _, cs in SPACEPORTS for c in cs}

# satcat status codes grouped by what happened to the object (interpreted from the catalogue; see paper)
STATUS_GROUP = {"R": "Re-entered", "R?": "Re-entered", "AR": "Re-entered", "D": "Deorbited on purpose",
                "L": "Landed or recovered", "L?": "Landed or recovered",
                "O": "Still in orbit", "OX": "Still in orbit", "AO": "Still in orbit",
                "DK": "Docked, berthed or joined another object", "GRP": "Docked, berthed or joined another object",
                "TFR": "Docked, berthed or joined another object", "ATT": "Docked, berthed or joined another object",
                "DSO": "Left Earth orbit", "DSA": "Left Earth orbit"}
TYPE_NAME = {"P": "Payloads (satellites and spacecraft)", "R": "Rocket stages", "C": "Components (shrouds, adapters, covers)",
             "D": "Debris fragments", "Z": "Catalogue errors and spare entries"}
TYPE_COL = {"P": "#2F5FA7", "R": "#C8322B", "C": "#E0A11B", "D": "#8C8478"}
EARTH_V = 465.1                # equatorial rotation speed, m/s (2 pi x 6,378.137 km / 86,164 s)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def read_gcat(name):
    """GCAT TSV: first line is the header (starting '#'), second a '# Updated' comment. All fields stripped strings."""
    import pandas as pd
    df = pd.read_csv(f"{RAW}/gcat_{name}.tsv", sep="\t", skiprows=[1], dtype=str, keep_default_na=False, quoting=3)
    df.columns = [c.lstrip("#").strip() for c in df.columns]
    return df.apply(lambda s: s.str.strip())
