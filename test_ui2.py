from playwright.sync_api import sync_playwright
import time

def test_admin_panel():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to /login...")
        page.goto("http://localhost:3000/login", wait_until="networkidle")
        
        print("Logging in...")
        page.fill('input[type="email"]', 'admin@kinochi.uz')
        page.fill('input[type="password"]', 'admin123')
        
        with page.expect_navigation():
            page.click('button[type="submit"]')
        
        print("Current URL:", page.url)
        
        print("Navigating to /movies...")
        page.goto("http://localhost:3000/movies", wait_until="load")
        page.wait_for_timeout(2000)
        
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type} {msg.text}") if msg.type == 'error' else None)
        page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))
        
        print("Opening Video Upload Modal for the first movie...")
        # Find the button with title="Video yuklash" or SVG that triggers it
        buttons = page.locator('button[title="Video yuklash"]').all()
        if buttons:
            buttons[0].click()
            print("Modal opened!")
            page.wait_for_timeout(2000)
            
            # Let's try switching sections
            print("Clicking 'Telegram Link/ID' section...")
            try:
                page.click('text="Telegram Link/ID"')
                page.wait_for_timeout(1000)
            except Exception as e:
                print("Failed to click Telegram Link/ID:", e)
                
            print("Clicking 'Fayl yuklash' section...")
            try:
                page.click('text="Fayl yuklash"')
                page.wait_for_timeout(1000)
            except Exception as e:
                print("Failed to click Fayl yuklash:", e)
                
        else:
            print("No video upload button found. Cannot test modal.")
            
        print("Done.")
        browser.close()

if __name__ == "__main__":
    test_admin_panel()
