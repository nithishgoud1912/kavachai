"""All tests use disposable stores, never the developer's databases or documents."""
import os
import tempfile
from pathlib import Path
TEST_ROOT = Path(tempfile.mkdtemp(prefix="kavachai-tests-"))
os.environ.update(SQLITE_DB_PATH=str(TEST_ROOT/'test.db'), CHROMA_DB_PATH=str(TEST_ROOT/'chroma'),
                  OBJECT_STORE_PATH=str(TEST_ROOT/'objects'), ALLOW_DEMO_SESSIONS='true',
                  OLLAMA_HOST='http://127.0.0.1:1', ENVIRONMENT='test')
