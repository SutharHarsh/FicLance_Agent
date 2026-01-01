import { chromium } from "playwright";
import path from "path";
import fs from "fs";

async function main() {
  const templatePath = process.argv[2];
  const outDir = process.argv[3];

  if (!fs.existsSync(templatePath)) {
    console.error("❌ template.html not found:", templatePath);
    process.exit(1);
  }

  const browser = await chromium.launch();
  const page = await browser.newPage();

  const fileUrl = "file://" + path.resolve(templatePath);

  try {
    await page.goto(fileUrl, { waitUntil: "load" });
  } catch (e) {
    console.error("goto error:", e);
    await browser.close();
    process.exit(1);
  }

  const outputFile = path.join(outDir, "static-screenshot.png");

  await page.screenshot({ path: outputFile });

  console.log(JSON.stringify([{ screenshot: outputFile }]));

  await browser.close();
}

main();
