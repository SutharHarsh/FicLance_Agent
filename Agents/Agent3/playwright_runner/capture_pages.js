// agents/agent3/playwright_runner/capture_pages.js
const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
  const raw = process.argv[2] || "[]";
  const routes = JSON.parse(raw);
  const browser = await chromium.launch({ args: ["--no-sandbox"] });
  const page = await browser.newPage();
  let results = [];
  for (const r of routes) {
    const pathSafe =
      r === "/"
        ? "root"
        : r.replace(/\//g, "_").replace(/[^a-zA-Z0-9_\-]/g, "");
    try {
      await page.goto(`http://localhost:3000${r}`, { timeout: 30000 });
      const out = `agents/agent3/playwright_runner/screenshot_${pathSafe}.png`;
      await page.screenshot({ path: out, fullPage: true });
      results.push({ route: r, screenshot: out });
    } catch (err) {
      results.push({ route: r, error: err.message });
    }
  }
  await browser.close();
  console.log(JSON.stringify(results));
})();
