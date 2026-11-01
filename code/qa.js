// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8797; set PORT to change).
const { chromium } = require("playwright");
// Leaflet from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here.
const LEAF = process.env.LEAFLET_DIST || "/dev/shm/nuclear/npm/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8797) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(2000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(600); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 1967; r.dispatchEvent(new Event("input")); });
    await p.click('#modeRow [data-m="year"]'); await p.waitForTimeout(800); await shot("#atlas", "map_1967");
    await p.click("#play"); await p.waitForTimeout(1500); await p.click("#play");
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 2025; r.dispatchEvent(new Event("input")); });
    await p.click("#blocRow .btn:nth-child(4)"); await p.waitForTimeout(800); await shot("#atlas", "map_2025_china");
    await p.click("#blocRow .btn:nth-child(2)"); await p.click('#modeRow [data-m="cum"]');
    await p.fill("#q", "Apollo 11"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2000); await shot("#atlas", "search_apollo");
    await p.fill("#q", "Kourou"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2000); await shot("#atlas", "port_kourou");
    await p.click("#focusRow .btn:last-child"); await p.waitForTimeout(2500); await shot("#atlas", "nemo");
    await p.click("#focusRow .btn:nth-child(2)"); await p.waitForTimeout(1200);
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    for (const c of ["yearChart", "failChart", "portChart", "portTable", "latChart", "downChart", "fateChart", "stationTable"]) await shot("#" + c, c);
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#yearChart", "dark_year");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
