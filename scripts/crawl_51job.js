const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

/**
 * 大连应届生招聘数据采集 v3（最终交付版）
 * 改进：抓取卡片全部标签（不截断）、区分福利标签与技能标签、保留完整文本
 */
const OUT = "/workspace/dalian-thesis/data_raw/list_jobs.json";
const KEYWORDS = [
  "大连 应届生", "大连 校招", "大连 毕业生", "大连 管培生", "大连 实习",
  "大连 本科 应届", "大连 硕士 应届", "大连 技术员 应届", "大连 软件 应届", "大连 机械 应届",
  "辽宁 大连 应届生", "大连 开发区 应届", "大连 高新 应届", "大连 财务 应届", "大连 销售 应届",
  "大连 化工 应届", "大连 船舶 应届", "大连 电子 应届", "大连 自动化 应届", "大连 生物 应届",
  "应届生", "校招", "管培生", "毕业生", "实习生",
];
const PAGES = 3;      // 每关键词尝试翻到第 3 页（点击下一页）
const WAIT = 4500;

(async () => {
  const b = await chromium.launch({ headless: true });
  const p = await b.newContext({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: 1440, height: 900 }, locale: "zh-CN",
  }).then(c => c.newPage());

  const seen = new Map();
  const log = [];

  async function grab() {
    return await p.evaluate(() => {
      const cards = Array.from(document.querySelectorAll(".joblist-item"));
      return cards.map(el => {
        const g = (s) => { const e = el.querySelector(s); return e ? e.innerText.trim() : ""; };
        const titleEl = el.querySelector(".jname");
        const tags = Array.from(el.querySelectorAll(".joblist-item-tags .tag")).map(t => t.innerText.trim()).filter(Boolean);
        const comp = Array.from(el.querySelectorAll(".bc .dc")).map(t => t.innerText.trim()).filter(Boolean);
        return {
          title: titleEl ? (titleEl.getAttribute("title") || titleEl.innerText.trim()) : "",
          salary: g(".sal"),
          area: g(".area"),
          company: g(".cname"),
          welfareTags: tags,                    // 完整标签，不截断
          compInfo: comp,
          rawText: el.innerText.replace(/\s+/g, " ").trim(),   // 完整卡片文本
        };
      });
    });
  }

  for (const kw of KEYWORDS) {
    const base = "https://we.51job.com/pc/search?keyword=" + encodeURIComponent(kw);
    try {
      await p.goto(base, { waitUntil: "domcontentloaded", timeout: 45000 });
      await p.waitForTimeout(WAIT);
    } catch (e) {
      log.push("[ERR-load] " + kw);
      continue;
    }
    for (let pg = 1; pg <= PAGES; pg++) {
      try {
        const rows = await grab();
        let add = 0, dl = 0;
        rows.forEach(r => {
          if (!r.title) return;
          const key = r.title + "|" + r.company + "|" + r.salary;
          if (seen.has(key)) return;
          seen.set(key, r); add++;
          if (/大连/.test(r.area)) dl++;
        });
        log.push(kw + " p" + pg + " → 卡片 " + rows.length + " 新增 " + add + " 大连 " + dl + " 累计 " + seen.size);
        if (pg === PAGES) break;
        // 尝试点击下一页
        const next = p.locator(".btn-next, [class*='btn-next']").last();
        if (await next.count()) {
          const disabled = await next.getAttribute("disabled").catch(() => null);
          const cls = await next.getAttribute("class").catch(() => "");
          if (disabled !== null || /disabled/.test(cls || "")) break;
          await next.click({ timeout: 5000 }).catch(() => {});
          await p.waitForTimeout(WAIT);
        } else break;
      } catch (e) {
        log.push("[ERR] " + kw + " p" + pg + " " + e.message.slice(0, 40));
        break;
      }
    }
    await p.waitForTimeout(1000);
  }

  const all = Array.from(seen.values());
  const dalian = all.filter(r => /大连/.test(r.area || ""));
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify({
    crawledAt: new Date().toISOString(),
    source: "前程无忧 51job（we.51job.com 公开搜索结果页）",
    method: "Playwright 无头浏览器渲染 + DOM 可见文本提取",
    scope: "以「大连」组合关键词检索；平台对未登录请求按出口 IP 定向推送城市，故实际返回以该 IP 所在城市为主，本数据集为全国应届生岗位基准样本",
    count: { all: all.length, dalian: dalian.length },
    dalian, other: all.filter(r => !/大连/.test(r.area || "")),
  }, null, 1));
  log.forEach(l => console.log(l));
  console.log("\n完成：总 " + all.length + " 条 | 大连 " + dalian.length);
  await b.close();
})();
