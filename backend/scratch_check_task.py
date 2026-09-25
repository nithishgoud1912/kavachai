import asyncio
from app.db.database import async_session
from app.db.sql_models import WorkbenchJob

async def check():
    async with async_session() as db:
        job = await db.get(WorkbenchJob, "64620eaf-cf6f-4e0c-a8a9-b392fb15b677")
        if job:
            print("Status:", job.status)
            print("Payload:", job.payload)
        else:
            print("Job not found in DB")

if __name__ == "__main__":
    asyncio.run(check())
