"""
Database Schemas for Job Portal

Each Pydantic model represents a collection in your database.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class Company(BaseModel):
    """
    Companies collection schema
    Collection: "company"
    """
    name: str = Field(..., description="Company name")
    website: Optional[str] = Field(None, description="Company website URL")
    location: Optional[str] = Field(None, description="Headquarters or primary location")
    logo_url: Optional[str] = Field(None, description="Company logo URL")
    description: Optional[str] = Field(None, description="About the company")

class Job(BaseModel):
    """
    Jobs collection schema
    Collection: "job"
    """
    title: str = Field(..., description="Job title")
    company_id: Optional[str] = Field(None, description="Reference to company _id as string")
    company_name: str = Field(..., description="Company name shown on listing")
    location: str = Field(..., description="City, Country or Remote")
    employment_type: str = Field(..., description="full-time, part-time, contract, internship")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary range")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary range")
    description: str = Field(..., description="Full job description")
    requirements: List[str] = Field(default_factory=list, description="Key requirements")
    tags: List[str] = Field(default_factory=list, description="Searchable tags/skills")
    is_active: bool = Field(True, description="Whether the job is open")
    posted_at: Optional[datetime] = Field(default=None, description="Posting date; auto if not provided")

class Application(BaseModel):
    """
    Applications collection schema
    Collection: "application"
    """
    job_id: str = Field(..., description="Reference to job _id as string")
    job_title: str = Field(..., description="Redundant for quick display")
    company_name: str = Field(..., description="Redundant for quick display")
    name: str = Field(..., description="Applicant full name")
    email: EmailStr = Field(..., description="Applicant email")
    resume_url: Optional[str] = Field(None, description="Link to resume")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    status: str = Field("submitted", description="submitted, reviewed, interviewed, offered, rejected")
