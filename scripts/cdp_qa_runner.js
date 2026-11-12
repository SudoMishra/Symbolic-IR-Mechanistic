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

    // Programmatic bounding-box and clipping audit for all SVG figures
    console.log("Measuring programmatic label & legend clipping across all SVG figures...");
    const FIGURES_TO_AUDIT = [
      "01_raw_vs_symbolic.svg",
      "02_evidence_funnel.svg",
      "02_evidence_funnel_mobile.svg",
      "03_musique_confirmation.svg",
      "03b_frontier_musique.svg",
      "04_reasoning_budget.svg",
      "04b_anthropic_reasoning.svg",
      "05_longproc.svg",
      "06_stage6_geometry.svg",
      "07_stage7_swaps.svg",
      "07b_stage7_patching.svg",
      "08_stage8_entities.svg",
      "09_trust_boundary.svg",
    ];

    auditResults.svgAudits = {};

    for (const fig of FIGURES_TO_AUDIT) {
      const p = path.join(ROOT, "blog/site/assets", fig);
      if (!fs.existsSync(p)) {
        console.warn(`Warning: SVG file not found: ${p}`);
        continue;
      }
      const content = fs.readFileSync(p, "utf8");

      // Navigate to blank page to ensure clean DOM slate
      await client.send("Page.navigate", { url: "about:blank" });
      await wait(100);
      const treeRes = await client.send("Page.getFrameTree");
      const frameId = treeRes.frameTree.frame.id;

      await client.send("Page.setDocumentContent", {
        frameId,
        html: `<!doctype html><html><head><style>body{margin:0;padding:0;background:#faf9f6} svg{display:block}</style></head><body>${content}</body></html>`,
      });
      await wait(200);

      const res = await client.send("Runtime.evaluate", {
        expression: `(() => {
          const svg = document.querySelector('svg');
          if (!svg) return { error: 'No svg element found' };
          const vb = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width > 0
            ? svg.viewBox.baseVal
            : { x: 0, y: 0, width: svg.width.baseVal ? svg.width.baseVal.value : 1400, height: svg.height.baseVal ? svg.height.baseVal.value : 900 };
          svg.setAttribute('width', vb.width);
          svg.setAttribute('height', vb.height);
          const sRect = svg.getBoundingClientRect();

          const texts = Array.from(document.querySelectorAll('text'));
          const textAudits = texts.map((t, idx) => {
            const r = t.getBoundingClientRect();
            const left = r.left - sRect.left;
            const right = r.right - sRect.left;
            const top = r.top - sRect.top;
            const bottom = r.bottom - sRect.top;
            return {
              idx,
              text: t.textContent.trim().slice(0, 45),
              left: Math.round(left * 10) / 10,
              right: Math.round(right * 10) / 10,
              top: Math.round(top * 10) / 10,
              bottom: Math.round(bottom * 10) / 10,
              clippedLeft: left < -1.0,
              clippedRight: right > sRect.width + 1.0,
              clippedTop: top < -1.0,
              clippedBottom: bottom > sRect.height + 1.0
            };
          });

          const clippedTexts = textAudits.filter(t => t.clippedLeft || t.clippedRight || t.clippedTop || t.clippedBottom);

          const rects = Array.from(document.querySelectorAll('rect'));
          const rectAudits = rects.map((rc, idx) => {
            const r = rc.getBoundingClientRect();
            const left = r.left - sRect.left;
            const right = r.right - sRect.left;
            const top = r.top - sRect.top;
            const bottom = r.bottom - sRect.top;
            return {
              idx,
              left: Math.round(left * 10) / 10,
              right: Math.round(right * 10) / 10,
              top: Math.round(top * 10) / 10,
              bottom: Math.round(bottom * 10) / 10,
              clippedLeft: left < -1.0,
              clippedRight: right > sRect.width + 1.0,
              clippedTop: top < -1.0,
              clippedBottom: bottom > sRect.height + 1.0
            };
          });
          const clippedRects = rectAudits.filter(r => r.clippedLeft || r.clippedRight || r.clippedTop || r.clippedBottom);

          const lefts = textAudits.map(t => t.left);
          const rights = textAudits.map(t => sRect.width - t.right);
          const tops = textAudits.map(t => t.top);
          const bottoms = textAudits.map(t => sRect.height - t.bottom);

          return {
            viewBox: { x: vb.x, y: vb.y, width: Math.round(sRect.width), height: Math.round(sRect.height) },
            totalTexts: texts.length,
            clippedTexts: clippedTexts.length,
            clippedTextSamples: clippedTexts.slice(0, 5),
            totalRects: rects.length,
            clippedRects: clippedRects.length,
            minMargin: {
              left: lefts.length ? Math.min(...lefts) : 0,
              right: rights.length ? Math.min(...rights) : 0,
              top: tops.length ? Math.min(...tops) : 0,
              bottom: bottoms.length ? Math.min(...bottoms) : 0
            }
          };
        })()`,
        returnByValue: true,
      });

      const auditVal = res.result.value;
      auditResults.svgAudits[fig] = auditVal;
      console.log(`  ${fig}: ${auditVal.totalTexts} texts (${auditVal.clippedTexts} clipped), ${auditVal.totalRects} rects (${auditVal.clippedRects} clipped)`);
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
