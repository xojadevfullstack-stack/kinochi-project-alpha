from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        def handle_response(response):
            if not response.ok:
                print(f"RESPONSE ERROR: {response.status} {response.url}")

        page.on("response", handle_response)

        try:
            print("Navigating to /movies...")
            page.goto("http://localhost:3000/movies", wait_until="networkidle")
            page.wait_for_timeout(2000)

            print("Navigating to /series...")
            page.goto("http://localhost:3000/series", wait_until="networkidle")
            page.wait_for_timeout(2000)

            print("Navigating to /pages...")
            page.goto("http://localhost:3000/pages", wait_until="networkidle")
            page.wait_for_timeout(2000)

            print("Test finished.")
        except Exception as e:
            print(f"TEST FAILED: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
