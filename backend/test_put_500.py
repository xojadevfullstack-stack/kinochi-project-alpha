import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        r_login = await client.post("https://kinochi-project-alpha.onrender.com/api/v1/auth/login", data={"username": "admin", "password": "admin_password_123"})
        token = r_login.json()["access_token"]
        print("Logged in")

        # Create a series to ensure we have one
        r_create = await client.post("https://kinochi-project-alpha.onrender.com/api/v1/series", 
            json={"title": "Test Series", "description": "", "poster_url": "", "imdb_rating": 0, "release_year": 2024, "director": "", "cast": "", "category_ids": [], "source_link": ""},
            headers={"Authorization": f"Bearer {token}"}
        )
        series_id = r_create.json()["id"]
        print("Created series:", series_id)

        # Update it with a source_link that has no topic
        r_update = await client.put(f"https://kinochi-project-alpha.onrender.com/api/v1/series/{series_id}",
            json={"title": "Test Series Update", "description": "", "poster_url": "", "imdb_rating": 0, "release_year": 2024, "director": "", "cast": "", "category_ids": [], "source_link": "https://t.me/c/4498937122/2"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Update status:", r_update.status_code)
        print("Update response:", r_update.text)

        # Clean up
        await client.delete(f"https://kinochi-project-alpha.onrender.com/api/v1/series/{series_id}", headers={"Authorization": f"Bearer {token}"})

asyncio.run(main())
