import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # First authenticate to get token
        login_resp = await client.post("https://kinochi-project-alpha.onrender.com/api/v1/auth/login", json={"username": "admin", "password": "password"})
        print("Login:", login_resp.status_code, login_resp.text)
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Post a channel
            payload = {
                "channel_username": "kinochi_mvp",
                "channel_title": "Kinochi Test",
                "is_active": True,
                "subscriber_limit": 200
            }
            res = await client.post("https://kinochi-project-alpha.onrender.com/api/v1/channels/", json=payload, headers=headers)
            print("Post channel:", res.status_code, res.text)
            
            # Get channels
            res2 = await client.get("https://kinochi-project-alpha.onrender.com/api/v1/channels/", headers=headers)
            print("Get channels:", res2.status_code, res2.text)

if __name__ == "__main__":
    asyncio.run(main())
