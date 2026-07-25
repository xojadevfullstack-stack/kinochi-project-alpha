const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));
  page.on('response', async response => {
    if (!response.ok()) {
      console.log(`RESPONSE ERROR: ${response.status()} ${response.url()}`);
      try {
        console.log(await response.text());
      } catch (e) {}
    }
  });

  try {
    console.log("Navigating to Admin Panel movies page...");
    await page.goto('http://localhost:3000/movies', { waitUntil: 'networkidle' });
    console.log("Waiting a bit...");
    await page.waitForTimeout(2000);
    
    console.log("Navigating to Series page...");
    await page.goto('http://localhost:3000/series', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log("Navigating to Pages page...");
    await page.goto('http://localhost:3000/pages', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log("Test finished.");
  } catch (error) {
    console.error("TEST FAILED:", error);
  } finally {
    await browser.close();
  }
})();
