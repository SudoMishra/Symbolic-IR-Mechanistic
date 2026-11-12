/**
 * High-fidelity CDP-based visual QA capture for blog/site/index.html.
 * Uses native Node 22 WebSocket to communicate with Chrome DevTools Protocol.
 */
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SITE_URL = `file://${path.join(ROOT, "blog/site/index.html")}`;
const OUT_DIR = path.join(ROOT, "results/qa/screenshots");

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => resolve(JSON.parse(data)));
    }).on("error", reject);
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.id = 1;
    this.pending = new Map();
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    };
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function run() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const chrome = spawn("google-chrome", [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--remote-debugging-port=9223",
    "about:blank",
  ]);

  try {
    await wait(1000);
    const version = await getJson("http://127.0.0.1:9223/json/version");
    const targets = await getJson("http://127.0.0.1:9223/json");
    const pageTarget = targets.find((t) => t.type === "page") || targets[0];

    const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.connect();

    await client.send("Page.enable");
    await client.send("DOM.enable");
    await client.send("CSS.enable");
    await client.send("Runtime.enable");

    const viewports = [
      { name: "mobile", width: 390, height: 844, scale: 1 },
      { name: "tablet", width: 768, height: 1024, scale: 1 },
      { name: "desktop", width: 1440, height: 900, scale: 1 },
    ];

    const auditResults = {
      timestamp: new Date().toISOString(),
      viewports: [],
      figures: [],
      overflowChecks: [],
    };

    for (const vp of viewports) {
      console.log(`Auditing viewport: ${vp.name} (${vp.width}x${vp.height})...`);
      await client.send("Emulation.setDeviceMetricsOverride", {
        width: vp.width,
        height: vp.height,
        deviceScaleFactor: vp.scale,
        mobile: vp.name === "mobile",
      });

      await client.send("Page.navigate", { url: SITE_URL });
      await wait(1200);

      // Measure layout
      const evalMetrics = await client.send("Runtime.evaluate", {
        expression: `({
          scrollWidth: document.documentElement.scrollWidth,
          scrollHeight: document.documentElement.scrollHeight,
          clientWidth: document.documentElement.clientWidth,
          hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
          overflowDiff: Math.max(0, document.documentElement.scrollWidth - window.innerWidth)
        })`,
        returnByValue: true,
      });

      const metrics = evalMetrics.result.value;

      // Viewport screenshot (above the fold)
      const vpShot = await client.send("Page.captureScreenshot", {
        format: "png",
        clip: { x: 0, y: 0, width: vp.width, height: vp.height, scale: 1 },
      });
      const vpFile = `site_${vp.name}_${vp.width}px_viewport.png`;
      fs.writeFileSync(path.join(OUT_DIR, vpFile), Buffer.from(vpShot.data, "base64"));

      // Full page screenshot
      const fullShot = await client.send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: true,
      });
      const fullFile = `site_${vp.name}_${vp.width}px_full.png`;
      fs.writeFileSync(path.join(OUT_DIR, fullFile), Buffer.from(fullShot.data, "base64"));

      auditResults.viewports.push({
        name: vp.name,
        width: vp.width,
        height: vp.height,
        viewportFile: vpFile,
        fullFile: fullFile,
        metrics,
      });

      console.log(`  Scroll dimensions: ${metrics.scrollWidth}x${metrics.scrollHeight}, Overflow diff: ${metrics.overflowDiff}px`);
    }

    // Capture each figure in context at desktop 1440px
    await client.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await client.send("Page.navigate", { url: SITE_URL });
    await wait(1200);

    const figNodes = await client.send("Runtime.evaluate", {
      expression: `Array.from(document.querySelectorAll('figure')).map((fig, idx) => {
        const img = fig.querySelector('img');
        const cap = fig.querySelector('figcaption');
        const rect = fig.getBoundingClientRect();
        return {
          idx,
          imgSrc: img ? img.getAttribute('src') : '',
          imgAlt: img ? img.getAttribute('alt') : '',
          capText: cap ? cap.innerText.slice(0, 100) : '',
          box: { x: rect.x + window.scrollX, y: rect.y + window.scrollY, width: rect.width, height: rect.height }
        };
      })`,
      returnByValue: true,
    });

    for (const f of figNodes.result.value) {
      if (!f.imgSrc || f.box.width <= 0 || f.box.height <= 0) continue;
      const baseName = path.basename(f.imgSrc, ".svg");
      const shot = await client.send("Page.captureScreenshot", {
        format: "png",
        clip: {
          x: Math.max(0, f.box.x - 10),
          y: Math.max(0, f.box.y - 10),
          width: Math.min(1440, f.box.width + 20),
          height: f.box.height + 20,
          scale: 1,
        },
      });
      const figFilename = `figure_context_${baseName}.png`;
      fs.writeFileSync(path.join(OUT_DIR, figFilename), Buffer.from(shot.data, "base64"));
      auditResults.figures.push({
        name: baseName,
        src: f.imgSrc,
        captionSnippet: f.capText,
        file: figFilename,
        width: Math.round(f.box.width),
        height: Math.round(f.box.height),
      });
    }

    client.close();

    fs.writeFileSync(
      path.join(ROOT, "results/qa/cdp_audit_summary.json"),
      JSON.stringify(auditResults, null, 2),
      "utf8"
    );
    console.log("CDP Visual QA capture finished successfully.");
  } finally {
    chrome.kill();
  }
}

run().catch((err) => {
  console.error("Error in CDP runner:", err);
  process.exit(1);
});
