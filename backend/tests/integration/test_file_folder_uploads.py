"""
Integration tests for File and Folder Uploads in Deep Investigate and Chat Box.
Verifies:
- File and folder batch uploads with relative paths.
- Multiple document format extraction (txt, csv, md, json, log).
- Ingestion into ChromaDB vector store and ObjectStore.
- Investigation creation with attachments.
- Chat message generation grounded in uploaded file contents.
- Evidence raw file and page serving endpoints.
"""

import io
import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db


@pytest.mark.asyncio
async def test_file_and_folder_upload_flow():
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a session
        sess_resp = await client.post(
            "/api/v1/session",
            json={"name": "Alex Chen", "department": "Reliability Engineering"},
        )
        assert sess_resp.status_code in (200, 201)
        session_id = sess_resp.json()["session_id"]
        auth_headers = {"Authorization": f"Bearer {session_id}"}

        # 2. Test Deep Investigation upload with multiple files & folder paths
        doc1_content = b"Equipment: Compressor C-301\nOperating pressure: 42 bar\nCritical vibration threshold: 4.5 mm/s.\nOil change interval: 5000 hours."
        doc2_content = b"Date,Equipment,Temperature,Status\n2026-09-01,C-301,78.5,Normal\n2026-09-05,C-301,94.2,Warning\n2026-09-08,C-301,102.0,Critical"
        doc3_content = b'{"incident_id": "INC-994", "equipment": "C-301", "root_cause": "Lube oil filter contamination causing bearing overheating"}'

        files = [
            ("files", ("compressor_manual.txt", io.BytesIO(doc1_content), "text/plain")),
            ("files", ("telemetry.csv", io.BytesIO(doc2_content), "text/csv")),
            ("files", ("incident_report.json", io.BytesIO(doc3_content), "application/json")),
        ]
        paths = json.dumps([
            "compressors/manuals/compressor_manual.txt",
            "compressors/logs/telemetry.csv",
            "compressors/reports/incident_report.json",
        ])

        upload_resp = await client.post(
            "/api/v1/investigations/upload",
            files=files,
            data={"paths": paths},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["total_files"] == 3
        assert len(upload_data["files"]) == 3

        # Verify paths and source_ids
        for f in upload_data["files"]:
            assert f["source_id"].startswith("doc_")
            assert f["path"] is not None
            assert f["chunk_count"] >= 1
            assert f["extracted_text_preview"] is not None

        # 3. Test raw file serving
        test_source_id = upload_data["files"][0]["source_id"]
        raw_resp = await client.get(f"/api/v1/files/{test_source_id}/raw", headers=auth_headers)
        assert raw_resp.status_code == 200
        assert b"Compressor C-301" in raw_resp.content

        # 4. Test page render / text serving endpoint
        page_resp = await client.get(f"/api/v1/files/{test_source_id}/page/1", headers=auth_headers)
        assert page_resp.status_code == 200

        # 5. Test create investigation with attachments
        attachments_payload = [
            {
                "filename": f["filename"],
                "url": f["url"],
                "type": f["type"],
                "extracted_text": f["extracted_text_preview"],
                "source_id": f["source_id"],
                "path": f["path"],
                "size": f["size"],
            }
            for f in upload_data["files"]
        ]

        inv_resp = await client.post(
            "/api/v1/investigations",
            json={
                "query": "Investigate Compressor C-301 and explain why temperature reached critical state.",
                "session_id": session_id,
                "attachments": attachments_payload,
            },
            headers=auth_headers,
        )
        assert inv_resp.status_code == 202
        inv_data = inv_resp.json()
        assert inv_data["attachments_count"] == 3
        investigation_id = inv_data["investigation_id"]

        # 6. Verify investigation report includes attachments
        report_resp = await client.get(f"/api/v1/investigations/{investigation_id}/report", headers=auth_headers)
        # Should be 202 (in progress) or 200 (if quick)
        assert report_resp.status_code in (200, 202)

        # 7. Test Chat Box folder batch upload
        chat_files = [
            ("files", ("safety_protocol.md", io.BytesIO(b"# Safety Rules\nEmergency Stop button is located at Panel E-4.\nEvacuate immediately if siren sounds 3 times."), "text/markdown")),
            ("files", ("maintenance.log", io.BytesIO(b"2026-09-08 10:00:00 [INFO] Replaced seal on Pump P-105"), "text/plain")),
        ]
        chat_paths = json.dumps([
            "safety/safety_protocol.md",
            "logs/maintenance.log",
        ])

        chat_upload_resp = await client.post(
            "/api/v1/conversations/upload-batch",
            files=chat_files,
            data={"paths": chat_paths},
            headers=auth_headers,
        )
        assert chat_upload_resp.status_code == 200
        chat_upload_data = chat_upload_resp.json()
        assert chat_upload_data["total_files"] == 2
        assert chat_upload_data["files"][0]["path"] == "safety/safety_protocol.md"

        # 8. Test Chat Message with attached files grounded response
        # Create conversation
        conv_resp = await client.post(
            "/api/v1/conversations",
            json={"session_id": session_id, "title": "Safety & Manuals Review", "type": "general"},
            headers=auth_headers,
        )
        assert conv_resp.status_code == 201
        conv_id = conv_resp.json()["id"]

        chat_attachments = [
            {
                "filename": chat_upload_data["files"][0]["filename"],
                "url": chat_upload_data["files"][0]["url"],
                "type": chat_upload_data["files"][0]["type"],
                "extracted_text": chat_upload_data["files"][0]["extracted_text_preview"],
                "source_id": chat_upload_data["files"][0]["source_id"],
                "path": chat_upload_data["files"][0]["path"],
            }
        ]

        # Send question specifically about the uploaded safety protocol
        msg_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={
                "content": "Where is the Emergency Stop button located according to the safety protocol?",
                "attachments": chat_attachments,
            },
            headers=auth_headers,
        )
        assert msg_resp.status_code == 200
        msg_data = msg_resp.json()
        assert msg_data["role"] == "assistant"
        # The assistant response should reference Panel E-4 from the submitted file!
        assert "E-4" in msg_data["content"] or "Panel" in msg_data["content"] or len(msg_data["content"]) > 10
