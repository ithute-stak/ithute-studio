from app.template_engine import generate_document


def template():
    return {"schemaVersion":1,"properties":{"title":"Test"},"settings":{},"header":{"type":"doc","content":[]},"footer":{"type":"doc","content":[]},"body":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"variable","attrs":{"path":"record.reference","format":"text"}}]},{"type":"dynamicTable","attrs":{"collectionPath":"items","columns":[{"label":"Description","path":"description"},{"label":"Qty","path":"quantity"}]}}]}}


def test_variables_and_dynamic_table_are_resolved():
    result = generate_document(
        template(),
        {
            "record": {"reference": "REF-100"},
            "items": [
                {"description": "One", "quantity": 2},
                {"description": "Two", "quantity": 3},
            ],
        },
    )
    assert result["body"]["content"][0]["content"][0]["text"] == "REF-100"
    table = result["body"]["content"][1]
    assert table["type"] == "table"
    assert len(table["content"]) == 3
    assert result["version"] == 1
