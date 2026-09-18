"""Document Studio worker contract.

The API owns project state and queues durable job/outbox records. Queue adapters can
translate those records into this neutral worker contract without coupling the Studio
core to a specific broker or product.
"""

from typing import Any, Literal

from pydantic import BaseModel

WorkerJobKind = Literal[
    "render",
    "bulk-generate",
    "thumbnail",
    "verify",
    "pdf-import",
    "pdf-export",
    "pdf-ocr",
    "pdf-index-images",
    "pdf-index-vectors",
    "webhook-delivery",
]


class Job(BaseModel):
    id: str
    kind: WorkerJobKind
    payload: dict[str, Any]


def run_job(job: Job) -> dict[str, Any]:
    """Broker-neutral dispatch boundary; concrete processors register behind this API."""
    return {
        "jobId": job.id,
        "status": "accepted",
        "kind": job.kind,
    }
