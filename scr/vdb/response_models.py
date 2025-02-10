from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import date

class RemoteWork(str, Enum):
    fully_remote = "fully_remote"
    partly_remote = "partly_remote"
    on_site = "on_site"

class JobDetails(BaseModel):
    location: Optional[str] = Field(None, description="The city or location (adress) of the job location.")
    start_date: Optional[date] = Field(None, description="The date the role starts in the format YYYY-MM-DD.")
    remote: Optional[RemoteWork] = Field(None, description="The remote work policy.")