"""Document Studio worker boundary.

Production queue adapters can call `run_job` for PDF/DOCX rendering, bulk generation,
thumbnailing and verification. No connector-specific logic belongs here.
"""
from typing import Any, Literal
from pydantic import BaseModel
class Job(BaseModel):
    id:str; kind:Literal["render","bulk-generate","thumbnail","verify"]; payload:dict[str,Any]
def run_job(job:Job)->dict[str,Any]:
    return {"jobId":job.id,"status":"accepted","kind":job.kind}
