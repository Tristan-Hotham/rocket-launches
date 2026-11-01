"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, pk, ob, lo, pt = R["source"], R["peaks"], R["objects"], R["located"], R["ports"]
N = lambda v: f"{round(v):,}"
readme = f"""# Up and down: every orbital launch since Sputnik, and where it all comes back

A map and analysis of all {N(s['n'])} orbital launch attempts from Sputnik (4 October 1957) to {s['last_date']} in Jonathan McDowell's General Catalog of Artificial Space Objects (GCAT): who launched them, from which of {s['n_ports']} spaceports, how often they failed, and what has come back down, including the spacecraft cemetery around Point Nemo in the South Pacific.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Launches: {N(s['n'])} orbital launch attempts, {N(s['fail'])} ({s['fail_pct']:.1f}%) failed. Cold War peak {pk['coldwar_n']} in {pk['coldwar_year']}; post Cold War low {pk['dip_n']} in {pk['dip_year']}; record {pk['record_n']} in {pk['record_year']} ({pk['record_vs_coldwar_pct']:.0f}% above the old peak, {pk['record_vs_dip_x']:.1f} times the low). {pk['since2020_pct']:.0f}% of all launches have happened since 2020.
- Who: SpaceX made {pk['spx_2025']} of the {pk['record_n']} attempts in {pk['record_year']} ({pk['spx_2025_pct']:.0f}%); China {pk['cn_2025']}; Russia {pk['ru_2025']}. Over the whole period the Soviet Union and Russia made {R['blocs']['Soviet Union and Russia']['pct']:.0f}% of attempts, the United States {R['blocs']['United States']['pct']:.0f}% and China {R['blocs']['China']['pct']:.0f}%.
- Spaceports: Plesetsk ({N(pt['Plesetsk']['n'])}), Baikonur ({N(pt['Baikonur']['n'])}), Cape Canaveral with Kennedy ({N(pt['Cape Canaveral and Kennedy']['n'])}) and Vandenberg ({N(pt['Vandenberg']['n'])}) hold {R['top4_share']:.0f}% of all attempts. In {pk['record_year']} Florida hosted {pt['Cape Canaveral and Kennedy']['y2025']} ({R['cape']['y2025_pct']:.0f}%); Mahia, New Zealand {pt['Mahia']['y2025']}, more than Baikonur ({pt['Baikonur']['y2025']}).
- Latitude: Earth's eastward push is {R['lat']['kourou_v']} m/s at Kourou, {R['lat']['baikonur_v']} m/s at Baikonur; {R['lat']['kourou_gto_pct']:.0f}% of Kourou's launches head towards geostationary orbit, {R['lat']['baikonur_gto_pct']:.0f}% of Baikonur's. Palmachim (Israel) launches only westward.
- Coming down: {N(ob['came_down'])} of {N(ob['n'])} catalogued objects ({ob['came_down_pct']:.0f}%) have come back; only {ob['deorbited']} were deliberately deorbited. Peak year {ob['down_peak_year']} ({N(ob['down_peak_n'])}, {N(R['asat']['y2022'])} of them Kosmos 1408 fragments). In {pk['record_year']}, {ob['down_2025_starlink_pct']:.0f}% of returns were Starlink satellites.
- Where: of {N(lo['reentered'])} uncontrolled re-entries with a GCAT place, {lo['unc_sea_pct']:.0f}% fell over the sea and {lo['unc_near_nemo_pct']:.1f}% within {N(lo['nemo_r_km'])} km of Point Nemo (a circle covering {lo['circle_share_pct']:.1f}% of the Earth). The spacecraft cemetery takes the few big controlled returns, not junk in general.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/launches.json` and `data/reentries.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/orbital_launches.csv` | All {N(s['n'])} orbital launch attempts: GCAT tag, date, vehicle, mission, GCAT site and spaceport (with coordinates), agency and its state, country or bloc, launch code, outcome, orbit class, first payload inclination, payloads and objects catalogued. |
| `data/spaceports.csv` | Per spaceport: host country, coordinates, attempts, failures, first and last year, busiest year, since 2020, 2025, rotation speed, direction shares, launches towards geostationary orbit. |
| `data/launches_by_year.csv` | Attempts, successes, failures, by bloc, SpaceX and payloads catalogued, per year. |
| `data/reentries_by_year.csv` | Catalogued objects that re-entered, were deorbited or landed, per year and type, and Starlink satellites among them. |
| `data/reentry_places.csv` | The {N(lo['n'])} objects whose place of re-entry or landing GCAT writes as coordinates, with the original text, land or sea, and distance to Point Nemo. |
| `data/objects_by_fate.csv` | Catalogued objects by type and fate. |
| `data/space_stations_fate.csv` | GCAT's record for every Salyut, Skylab, Mir and Tiangong station. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/launches.json`, `data/reentries.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Orbital launch attempt: GCAT launch code O (orbital) or D (deep space), excluding OE (pad explosion before launch, {s['pad_oe']}) and OA (abort before lift-off, {s['abort_oa']}). Failure: outcome F, including partial failures. Earlier suborbital flights, including {N(R['before']['v2'])} German A-4 (V-2) launches from {R['before']['v2_first']}, are context only.
- Who launched: state of the first agency GCAT lists (orgs.tsv), grouped into eight blocs. This is GCAT's agency view, so Rocket Lab counts for New Zealand and Starsem's Soyuz flights from Baikonur for Europe.
- Spaceports: GCAT site codes merged where renamed or adjacent (e.g. NIIP-5 and GIK-5 at Baikonur; Cape Canaveral with Kennedy). Air launches at the airfield.
- Direction: inclination of the first payload (successful launches to low and medium orbit). GCAT has no launch azimuths.
- Fates: satcat status grouped (R re-entered, D deorbited, L landed, DK docked...). Re-entry places only where GCAT's destination field gives coordinates; nothing inferred. The 2,500 km circle around Point Nemo is an indicative device, not a boundary.
- Caveats: GCAT judgements are followed; the main catalogue omits objects without standard catalogue numbers; fates after docking (cargo ship deorbits) are in GCAT's event catalogues, not used; {s['last_year']} is partial (to {s['last_date']}).

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place (paths in `code/common.py`): GCAT TSVs and Wikipedia pages in `/home/claude/newdata/raw8/launches/`, Natural Earth in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/rocketlaunches/work` (set `RLTMP` to change).

```
python3 code/01_clean.py        # read GCAT, orbital attempts, blocs, spaceports, object fates and places
python3 code/02_geo.py          # outlines and city labels
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Jonathan C. McDowell, General Catalog of Artificial Space Objects (GCAT), release {s['release']}, {GCAT_URL}. CC BY 4.0. Data from GCAT (J. McDowell, planet4589.org/space/gcat).
- Wikipedia: "Pole of inaccessibility" (Point Nemo), "Spacecraft cemetery", "Spaceport", "List of rocket launch sites". CC BY-SA 4.0. Used for facts quoted in the text; no Wikipedia text is reproduced.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Up and down: seventy years of orbital launches and where space hardware comes back to Earth. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/meteorite-falls/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The launch and object data are
derived from Jonathan C. McDowell's General Catalog of Artificial Space Objects
(GCAT, planet4589.org/space/gcat), CC BY 4.0: please credit "Data from GCAT
(J. McDowell, planet4589.org/space/gcat)". Facts about Point Nemo come from
Wikipedia (CC BY-SA 4.0). Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every orbital rocket launch since Sputnik: {N(s['n'])} attempts. The Cold War record of {pk['coldwar_n']} a year stood until {pk['first_over_coldwar']}; in {pk['record_year']} the world launched {pk['record_n']}, more than half of them SpaceX's

## Body

I mapped all {N(s['n'])} orbital launch attempts in Jonathan McDowell's GCAT catalogue, from Sputnik in 1957 to {s['last_date'][:4]}, by spaceport and by who launched them. Plesetsk in northern Russia is the busiest site ever ({N(pt['Plesetsk']['n'])}), almost all during the Cold War; in {pk['record_year']} it managed {pt['Plesetsk']['y2025']}, while Florida hosted {pt['Cape Canaveral and Kennedy']['y2025']}. Launches fell to {pk['dip_n']} in {pk['dip_year']} after the Soviet collapse, then exploded with reusable Falcon 9s: {pk['since2020_pct']:.0f}% of all launches in seventy years have happened since 2020. About half of the {N(ob['n'])} catalogued objects have already fallen back, but only {ob['deorbited']} were steered down on purpose; Point Nemo, the spacecraft cemetery in the South Pacific, takes the big ones like Mir. Caveats: "who launched" is GCAT's launch agency (so Rocket Lab counts as New Zealand); {s['last_year']} is partial. Interactive map with a play button, country filter and re-entry places: {PAGE}

## Source comment

Source: GCAT, the General Catalog of Artificial Space Objects by Jonathan C. McDowell (planet4589.org/space/gcat, CC BY 4.0), release {s['release']}: launch list, sites, organisations and object catalogue. Orbital attempt = GCAT launch code O or D, excluding pad explosions and aborts before lift-off. Point Nemo position and spacecraft cemetery facts: Wikipedia. Outlines: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
