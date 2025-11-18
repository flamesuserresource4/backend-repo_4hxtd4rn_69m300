import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Job, Company, Application

app = FastAPI(title="Job Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Job Portal API is running"}


# Public: list jobs with filters
@app.get("/jobs")
def list_jobs(q: Optional[str] = None, location: Optional[str] = None, tag: Optional[str] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {"is_active": True}
    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}
    if tag:
        filter_query["tags"] = {"$in": [tag]}
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"company_name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]

    jobs = get_documents("job", filter_query, limit)
    # Convert ObjectId to str
    for j in jobs:
        j["_id"] = str(j["_id"]) if "_id" in j else None
        if "posted_at" in j and isinstance(j["posted_at"], datetime):
            j["posted_at"] = j["posted_at"].isoformat()
    return {"items": jobs}


# Admin: create job
@app.post("/jobs")
def create_job(job: Job):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    data = job.model_dump()
    if not data.get("posted_at"):
        data["posted_at"] = datetime.utcnow()
    job_id = create_document("job", data)
    return {"id": job_id}


# Public: get job detail
@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    from bson import ObjectId
    try:
        doc = db["job"].find_one({"_id": ObjectId(job_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Job not found")
        doc["_id"] = str(doc["_id"])  # type: ignore
        if "posted_at" in doc and isinstance(doc["posted_at"], datetime):
            doc["posted_at"] = doc["posted_at"].isoformat()
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")


# Public: submit application
@app.post("/applications")
def submit_application(apply: Application):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Optional: validate job exists
    from bson import ObjectId
    try:
        job_obj = db["job"].find_one({"_id": ObjectId(apply.job_id)})
        if not job_obj:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")

    app_id = create_document("application", apply)
    return {"id": app_id}


# Admin: list applications for a job
@app.get("/applications")
def list_applications(job_id: Optional[str] = None, limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_query = {}
    if job_id:
        filter_query["job_id"] = job_id
    apps = get_documents("application", filter_query, limit)
    for a in apps:
        a["_id"] = str(a["_id"]) if "_id" in a else None
    return {"items": apps}


# Optional helpers for companies
@app.post("/companies")
def create_company(company: Company):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    comp_id = create_document("company", company)
    return {"id": comp_id}

@app.get("/companies")
def list_companies(limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    comps = get_documents("company", {}, limit)
    for c in comps:
        c["_id"] = str(c["_id"]) if "_id" in c else None
    return {"items": comps}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
