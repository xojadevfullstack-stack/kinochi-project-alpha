import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_flow():
    print("Starting collection subscription test flow...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch collections
        res = await client.get("/api/v1/collections")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        cols = res.json()
        print(f"1. Fetched {len(cols)} collections.")
        if not cols:
            print("No collections in DB to test with. Exiting.")
            return

        col = cols[0]
        col_id = col["id"]
        print(f"Testing with collection ID={col_id} ('{col['name']}', category_type='{col.get('category_type')}')")

        test_user_id = 99999999

        # 2. Check initial status (should be false)
        res = await client.get(f"/api/v1/collections/{col_id}/subscription-status?telegram_user_id={test_user_id}")
        assert res.status_code == 200
        print(f"2. Initial status: is_subscribed={res.json()['is_subscribed']}")

        # 3. Toggle subscribe (should become True)
        res = await client.post(f"/api/v1/collections/{col_id}/subscribe", json={"telegram_user_id": test_user_id})
        assert res.status_code == 200
        data = res.json()
        assert data["is_subscribed"] is True
        print("3. Subscribed successfully: is_subscribed=True")

        # 4. Check status again
        res = await client.get(f"/api/v1/collections/{col_id}/subscription-status?telegram_user_id={test_user_id}")
        assert res.status_code == 200
        assert res.json()["is_subscribed"] is True
        print("4. Verified subscription status is True")

        # 5. Check user profile summary
        res = await client.get(f"/api/v1/users/by-telegram/{test_user_id}/summary")
        if res.status_code == 200:
            summary = res.json()
            col_subs = summary.get("collection_subscriptions", [])
            print(f"5. User profile summary contains {len(col_subs)} collection subscriptions.")
            assert any(cs["collection_id"] == col_id for cs in col_subs)
            print("   -> Match confirmed in profile!")
        else:
            print(f"5. User profile endpoint returned {res.status_code} (User might not exist in users table yet)")

        # 6. Unsubscribe (toggle again)
        res = await client.post(f"/api/v1/collections/{col_id}/subscribe", json={"telegram_user_id": test_user_id})
        assert res.status_code == 200
        data = res.json()
        assert data["is_subscribed"] is False
        print("6. Unsubscribed successfully: is_subscribed=False")

        # 7. Final status check
        res = await client.get(f"/api/v1/collections/{col_id}/subscription-status?telegram_user_id={test_user_id}")
        assert res.status_code == 200
        assert res.json()["is_subscribed"] is False
        print("7. Verified status is False.")

    print("\nALL COLLECTION SUBSCRIPTION TESTS PASSED SUCCESSFULLY! ✅")


if __name__ == "__main__":
    asyncio.run(test_flow())
