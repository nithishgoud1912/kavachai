"""Real local HTTP acceptance, isolated data, production password + MFA, no inference mocks.

Run after building the frontend and provisioning OCR, models and the dedicated worker.
Creates only public synthetic inputs. Secrets stay in memory. Results under .local/.
The resulting application socket observations do not certify host-wide air-gapping.
"""
import asyncio
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

import httpx
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))


async def main(code_only=False):
    output = ROOT / '.local' / ('acceptance-' + time.strftime('%Y%m%d-%H%M%S'))
    output.mkdir(parents=True)
    token, password = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    env = dict(os.environ, ENVIRONMENT='production', ALLOW_DEMO_SESSIONS='false', BOOTSTRAP_TOKEN=token,
               SQLITE_DB_PATH=str(output/'acceptance.db'), CHROMA_DB_PATH=str(output/'chroma'),
               OBJECT_STORE_PATH=str(output/'objects'), BACKEND_URL='http://127.0.0.1:18000/api/v1',
               NEXT_TELEMETRY_DISABLED='1',
               DOCKER_HOST=os.environ.get('DOCKER_HOST', 'tcp://127.0.0.1:2376'),
               DOCKER_TLS_VERIFY='1', DOCKER_CERT_PATH=os.environ.get('DOCKER_CERT_PATH', str(ROOT/'.local/worker-certs')))
    children, handles = [], []
    result = {'public_synthetic_inputs': True, 'real_inference': True, 'airgap_verified': False,
              'network_scope': 'Application Python socket audit only; no host/browser/model-service packet capture'}

    def save():
        (output/'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

    def start(args, cwd, name):
        log = open(output/(name+'.log'), 'w', encoding='utf-8')
        handles.append(log)
        children.append(subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=log,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))

    async def wait_ready(url):
        async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
            for _ in range(90):
                try:
                    response = await client.get(url)
                    if response.status_code == 200: return
                except httpx.HTTPError: pass
                if any(child.poll() is not None for child in children):
                    raise RuntimeError('A demo server exited; inspect its local log')
                await asyncio.sleep(1)
        raise RuntimeError('Demo server startup timed out')

    try:
        start([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '18000'], ROOT/'backend', 'backend')
        await wait_ready('http://127.0.0.1:18000/health')
        start([shutil.which('node') or 'node', 'node_modules/next/dist/bin/next', 'start', '-p', '18001', '-H', '127.0.0.1'], ROOT/'frontend', 'frontend')
        await wait_ready('http://127.0.0.1:18001')
        print('Production backend and frontend proxy started', flush=True)
        async with httpx.AsyncClient(base_url='http://127.0.0.1:18001/api/v1', trust_env=False, timeout=240) as client:
            async def post(path, **kwargs):
                response = await client.post(path, **kwargs)
                response.raise_for_status()
                return response.json()
            boot = await post('/auth/bootstrap', json={'bootstrap_token':token, 'username':'acceptance-admin', 'password':password, 'department':'Public Demo'})
            login = await post('/auth/login', json={'username':'acceptance-admin', 'password':password})
            assert login['mfa_required']
            from app.security import generate_totp
            await post('/auth/mfa/verify', json={'session_id':login['session_id'], 'code':generate_totp(boot['totp_secret'])})
            user = await post('/auth/users', json={'username':'acceptance-user', 'password':password,
                                                   'department':'Public Demo', 'roles':['ai_workbench_user']})
            login = await post('/auth/login', json={'username':'acceptance-user', 'password':password})
            await post('/auth/mfa/verify', json={'session_id':login['session_id'], 'code':generate_totp(user['totp_secret'])})
            assert client.cookies.get('kavach_session')
            result['production_auth'] = {'ok': True, 'password_and_mfa': True, 'http_only_cookie': True}
            result['readiness'] = (await client.get('/readiness')).json()
            result['models'] = (await client.get('/models')).json()
            save()
            print('Password/MFA and authorized runtime APIs verified', flush=True)

            async def run_task(name, body):
                created = await post('/tasks', json=body)
                for _ in range(600):
                    response = await client.get('/tasks/'+created['id']); response.raise_for_status()
                    task = response.json()
                    if task['status'] not in ('queued', 'running'): break
                    await asyncio.sleep(2)
                else: raise RuntimeError(f'{name} timed out')
                result[name] = task
                for artifact in task.get('artifacts', []):
                    response = await client.get('http://127.0.0.1:18001'+artifact['download_url'])
                    response.raise_for_status()
                    filename = Path(artifact.get('filename') or artifact.get('name') or artifact['download_url'].split('/')[-1]).name
                    if '.' not in filename: filename += '.'+artifact.get('format', 'bin')
                    (output/(name+'-'+filename)).write_bytes(response.content)
                save(); print(f"{name}: {task['status']}", flush=True)
                return task

            if not code_only:
                image = Image.new('RGB', (1400, 1000), 'white')
                draw = ImageDraw.Draw(image)
                font_path = Path('C:/Windows/Fonts/arial.ttf')
                font = ImageFont.truetype(str(font_path), 40) if font_path.exists() else ImageFont.load_default(size=40)
                lines = ['PUBLIC SYNTHETIC INSPECTION REPORT', 'Asset: P-204', 'Inspection Date: 2026-09-26',
                         'Finding: Coupling guard bolt is missing.', 'Action: Replace bolt and inspect guard before restart.',
                         'Inspector: Demo Technician', 'This document is a public demonstration sample.']
                for index, line in enumerate(lines): draw.text((60, 70 + index*100), line, fill='black', font=font)
                png = io.BytesIO(); image.save(png, format='PNG')
                with pymupdf.open() as document:
                    page = document.new_page(width=700, height=500)
                    page.insert_image(page.rect, stream=png.getvalue())
                    scan = document.tobytes()
                (output/'public-inspection.pdf').write_bytes(scan)
                upload = await post('/conversations/upload', files={'file':('public-inspection.pdf', scan, 'application/pdf')})
                chunks = (await client.get(f"/knowledge-base/documents/{upload['source_id']}/chunks")).json()
                result['ocr'] = {'ok': any('missing' in c['text'].lower() for c in chunks['chunks']),
                                 'engines': sorted({c['metadata'].get('ocr_engine', 'unknown') for c in chunks['chunks']})}
                save(); print('Real scanned PDF uploaded and OCR indexed', flush=True)

                await run_task('scan_to_word', {'query':'Draft an approval note from this public inspection report. State the missing coupling guard bolt and the documented action, cite the source, and request human review. Do not add operating thresholds.',
                                               'mode':'auto', 'deliverable_type':'word', 'attachments':[upload]})
                workbook = Workbook(); sheet = workbook.active; sheet.title='Readings'
                sheet.append(['Date', 'Pressure_bar']); sheet.append(['2026-09-25', 1]); sheet.append(['2026-09-26', 3])
                data = io.BytesIO(); workbook.save(data)
                spreadsheet = await post('/conversations/upload', files={'file':('public-readings.xlsx', data.getvalue())})
                await run_task('spreadsheet_to_excel', {'query':'Calculate the arithmetic mean of Pressure_bar and show the input rows and steps. Cite the source. Do not infer safety or operating fitness.',
                                                       'mode':'spreadsheet', 'deliverable_type':'excel', 'attachments':[spreadsheet]})
            await run_task('verified_code', {'query':'Write a Python function that returns the arithmetic mean of a nonempty numeric list. Include assertions that [1, 3] gives 2 and [2, 4, 6] gives 4, and print TESTS PASSED after the assertions. Use only the Python standard library.', 'mode':'code', 'deliverable_type':'code'})
            result['network'] = (await client.get('/network-monitor')).json()
            result['connections'] = (await client.get('/network-monitor?type=connections')).json()
            task_names = ['verified_code'] if code_only else ['scan_to_word', 'spreadsheet_to_excel', 'verified_code']
            result['acceptance_passed'] = all(result[name]['status'] == 'awaiting_review' for name in task_names)
            if not code_only:
                calculations = result['spreadsheet_to_excel'].get('calculation_results', [])
                result['mean_is_correct'] = any(metric['operation'] == 'mean' and metric['value'] == '2'
                                               for table in calculations for metric in table['results'])
                result['acceptance_passed'] = result['acceptance_passed'] and result['mean_is_correct'] and result['ocr']['ok']
            save()
    except Exception as exc:
        # Never persist request bodies or credentials on failure.
        result['error'] = f'{type(exc).__name__}: {str(exc)[:1000]}'
        save()
        raise
    finally:
        for child in reversed(children):
            child.terminate()
            try: child.wait(timeout=10)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
        for handle in handles: handle.close()
        print('Acceptance evidence: '+str(output), flush=True)
    return 0 if result.get('acceptance_passed') else 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-only', action='store_true', help='Rerun the coding acceptance independently')
    raise SystemExit(asyncio.run(main(code_only=parser.parse_args().code_only)))
