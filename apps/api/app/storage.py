from __future__ import annotations
import json, os, sqlite3, threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_DB = Path(os.getenv("DOCUMENT_STUDIO_DB", str(Path(__file__).resolve().parent.parent / "document_studio.sqlite3")))
_LOCK = threading.RLock()

def _now() -> str: return datetime.now().astimezone().isoformat()
def _connection() -> sqlite3.Connection:
    con=sqlite3.connect(_DB, check_same_thread=False); con.row_factory=sqlite3.Row; return con

def init_db() -> None:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK, _connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS templates(
          id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'custom',
          payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents(
          id TEXT PRIMARY KEY, title TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
          payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        ''')

def list_templates() -> list[dict[str,Any]]:
    with _LOCK, _connection() as con:
        return [json.loads(r['payload']) for r in con.execute('SELECT payload FROM templates ORDER BY updated_at DESC')]

def get_template(template_id:str) -> dict[str,Any] | None:
    with _LOCK, _connection() as con:
        row=con.execute('SELECT payload FROM templates WHERE id=?',(template_id,)).fetchone(); return json.loads(row['payload']) if row else None

def put_template(payload:dict[str,Any], template_id:str|None=None) -> dict[str,Any]:
    now=_now(); item=dict(payload); item['id']=template_id or str(item.get('id') or uuid4()); item.setdefault('name','Untitled template'); item.setdefault('category','custom'); item.setdefault('createdAt',now); item['updatedAt']=now
    with _LOCK, _connection() as con:
        con.execute('INSERT INTO templates(id,name,category,payload,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,category=excluded.category,payload=excluded.payload,updated_at=excluded.updated_at',(item['id'],item['name'],item['category'],json.dumps(item),item['createdAt'],item['updatedAt']))
    return item

def delete_template(template_id:str)->bool:
    with _LOCK, _connection() as con:
        cur=con.execute('DELETE FROM templates WHERE id=?',(template_id,)); return cur.rowcount>0

def list_documents() -> list[dict[str,Any]]:
    with _LOCK, _connection() as con:
        return [json.loads(r['payload']) for r in con.execute('SELECT payload FROM documents ORDER BY updated_at DESC')]

def get_document(document_id:str)->dict[str,Any]|None:
    with _LOCK, _connection() as con:
        row=con.execute('SELECT payload FROM documents WHERE id=?',(document_id,)).fetchone(); return json.loads(row['payload']) if row else None

def create_document(payload:dict[str,Any])->dict[str,Any]:
    now=_now(); item=dict(payload); item['id']=str(item.get('id') or uuid4()); item.setdefault('schemaVersion',1); item.setdefault('createdAt',now); item['updatedAt']=now; item['version']=int(item.get('version') or 1)
    title=str((item.get('properties') or {}).get('title') or 'Untitled document')
    with _LOCK, _connection() as con: con.execute('INSERT INTO documents(id,title,version,payload,created_at,updated_at) VALUES(?,?,?,?,?,?)',(item['id'],title,item['version'],json.dumps(item),item['createdAt'],item['updatedAt']))
    return item

def save_document(document_id:str,payload:dict[str,Any],expected_version:int|None=None)->dict[str,Any]|None:
    with _LOCK, _connection() as con:
        row=con.execute('SELECT version,created_at FROM documents WHERE id=?',(document_id,)).fetchone()
        if not row:return None
        if expected_version is not None and int(row['version'])!=expected_version: raise ValueError('version_conflict')
        item=dict(payload); item['id']=document_id; item['createdAt']=item.get('createdAt') or row['created_at']; item['updatedAt']=_now(); item['version']=int(row['version'])+1
        title=str((item.get('properties') or {}).get('title') or 'Untitled document')
        con.execute('UPDATE documents SET title=?,version=?,payload=?,updated_at=? WHERE id=?',(title,item['version'],json.dumps(item),item['updatedAt'],document_id)); return item
