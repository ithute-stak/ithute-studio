from fastapi.testclient import TestClient
from app.main import app

def test_template_crud_and_generation():
    with TestClient(app) as client:
        template={"name":"Generic letter","category":"general-business","document":{"schemaVersion":1,"workspaceId":"default","properties":{"title":"Letter"},"settings":{},"header":{"type":"doc","content":[]},"body":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"variable","attrs":{"path":"contact.fullName"}}]}]},"footer":{"type":"doc","content":[]},"variables":{},"version":1}}
        created=client.post('/v1/templates',json=template); assert created.status_code==201
        tid=created.json()['id']
        generated=client.post('/v1/documents/from-template',json={"templateId":tid,"data":{"contact":{"fullName":"Sample Person"}}}); assert generated.status_code==201
        body=generated.json()['body']; assert body['content'][0]['content'][0]['text']=='Sample Person'

def test_document_optimistic_versioning():
    with TestClient(app) as client:
        doc={"schemaVersion":1,"workspaceId":"default","properties":{"title":"One"},"settings":{},"header":{"type":"doc","content":[]},"body":{"type":"doc","content":[]},"footer":{"type":"doc","content":[]},"variables":{},"version":1}
        created=client.post('/v1/documents',json=doc).json(); did=created['id']
        saved=client.put(f'/v1/documents/{did}',json={"document":created,"expectedVersion":1}); assert saved.status_code==200; assert saved.json()['version']==2
        conflict=client.put(f'/v1/documents/{did}',json={"document":created,"expectedVersion":1}); assert conflict.status_code==409
