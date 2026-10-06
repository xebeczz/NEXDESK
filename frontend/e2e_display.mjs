import { chromium } from "playwright";
const BASE = "http://localhost:5173";
const TICKET = "14a48033-3929-423f-8abc-61b333a1459b"; // TCK-20260812-0005

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext();
await ctx.clearCookies();
const page = await ctx.newPage();
const net = [];
page.on("response", (r) => { if (r.url().includes("/assign")) net.push(`[${r.status()}] ${r.request().method()} ${r.url()}`); });

const log = (...a) => console.log(...a);

async function login() {
  await page.goto(BASE + "/login", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);
  await page.click('button:has-text("Admin")');
  await page.fill("#identifier", "admin@itdesk.io");
  await page.fill("#password", "Admin@12345");
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2200);
}
const dropdownText = () =>
  page.evaluate(() => {
    const t = document.querySelector('[role="combobox"]');
    return t ? t.innerText.trim() : "<none>";
  });
const dumpTrigger = () =>
  page.evaluate(() => {
    const t = document.querySelector('[role="combobox"]');
    return t ? t.outerHTML : "<none>";
  });
const openSelect = async () => {
  await page.waitForSelector('[role="combobox"]', { timeout: 10000 });
  await page.locator('[role="combobox"]').click();
  await page.waitForTimeout(700);
};

// TEST 1: open unassigned ticket -> "Select admin"
await login();
await page.goto(BASE + "/tickets/" + TICKET, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(3500);
log("TEST 1 URL:", page.url());
const debug = await page.evaluate(() => ({
  bodyLen: document.body.innerText.length,
  hasAssignLabel: document.body.innerText.includes("Assign to admin"),
  hasCombobox: !!document.querySelector('[role="combobox"]'),
  snippet: document.body.innerText.slice(0, 300),
}));
log("TEST 1 DEBUG:", JSON.stringify(debug));
log("TEST 1 (unassigned):", JSON.stringify(await dropdownText()));
log("TRIGGER HTML T1:", (await dumpTrigger()).replace(/class="[^"]*"/g, "").slice(0, 500));

// TEST 2: assign shanks -> shows "shanks"
await openSelect();
await page.click('[role="option"]:has-text("shanks")');
await page.locator('button:has(svg.lucide-user-plus)').click();
await page.waitForTimeout(2500);
log("TEST 2 (after assign shanks):", JSON.stringify(await dropdownText()));
log("TRIGGER HTML T2:", (await dumpTrigger()).slice(0, 400));

// TEST 3: refresh -> still "shanks"
await page.reload({ waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);
log("TEST 3 (after refresh):", JSON.stringify(await dropdownText()));

// TEST 4: leave + reopen -> still "shanks"
await page.goto(BASE + "/tickets", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(1500);
await page.goto(BASE + "/tickets/" + TICKET, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);
log("TEST 4 (reopen):", JSON.stringify(await dropdownText()));

// TEST 5: change to System Administrator -> shows "System Administrator"
await openSelect();
await page.click('[role="option"]:has-text("System Administrator")');
await page.locator('button:has(svg.lucide-user-plus)').click();
await page.waitForTimeout(2500);
log("TEST 5 (change to System Administrator):", JSON.stringify(await dropdownText()));

// TEST 6: refresh again -> still "System Administrator"
await page.reload({ waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);
log("TEST 6 (refresh after change):", JSON.stringify(await dropdownText()));

await browser.close();

log("\nASSIGN NETWORK:");
net.forEach((n) => log(n));

