from __future__ import annotations
from typing import Any
import httpx
class IthuteDocumentStudioClient:
    def __init__(self, base_url:str, token:str|None=None): self.base_url=base_url.rstrip('/'); self.token=token
    def generate_from_template(self, template:dict[str,Any], data:dict[str,Any], source:dict[str,Any]|None=None)->dict[str,Any]:
        headers={"authorization":f"Bearer {self.token}"} if self.token else {}
        response=httpx.post(f"{self.base_url}/v1/documents/from-template",json={"template":template,"data":data,"source":source},headers=headers,timeout=30);response.raise_for_status();return response.json()
