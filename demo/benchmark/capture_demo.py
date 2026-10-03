"""Optional Chrome smoke check and screenshots; no browser package downloads."""
import asyncio
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.request import urlopen
import websockets

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'screenshots'


async def inspect(url):
    tabs = json.load(urlopen('http://127.0.0.1:9226/json'))
    async with websockets.connect(next(t for t in tabs if t['type'] == 'page')['webSocketDebuggerUrl'], max_size=20_000_000) as ws:
        number = 0
        errors = []
        async def call(method, params=None):
            nonlocal number
            number += 1; target = number
            await ws.send(json.dumps({'id': target, 'method': method, 'params': params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('method') == 'Runtime.exceptionThrown': errors.append(msg['params'])
                if msg.get('id') == target:
                    if 'error' in msg: raise RuntimeError(msg['error'])
                    return msg.get('result', {})
        async def evaluate(expression):
            result = await call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
            if 'exceptionDetails' in result: raise AssertionError(result['exceptionDetails'])
            return result.get('result', {}).get('value')
        async def settle():
            await asyncio.sleep(.35)
            await evaluate("Promise.all(Array.from(document.images).map(i=>i.complete?Promise.resolve():new Promise(r=>{i.onload=r;i.onerror=r})))")
            assert not await evaluate("document.querySelector('main').innerText.includes('No se pudo cargar')")
            assert await evaluate('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)'), 'Broken image'
        async def capture(name):
            await settle()
            result = await call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
            (OUT / (name + '.png')).write_bytes(base64.b64decode(result['data']))
        await call('Runtime.enable'); await call('Page.enable')
        await call('Emulation.setDeviceMetricsOverride', {'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
        navigation = await call('Page.navigate', {'url': url})
        assert not navigation.get('errorText'), navigation
        for _ in range(100):
            if await evaluate("!!document.querySelector('nav button')"): break
            await asyncio.sleep(.1)
        assert await evaluate("!!document.querySelector('nav button')"), await evaluate('document.documentElement.outerHTML')
        await capture('01_overview')
        for page in ['explorer','conditions','packet','leakage','repro','tests','c2','narratives','next']:
            await evaluate(f"document.querySelector('[data-page={page}]').click()")
            await settle()
            print('PASS page', page)
        await evaluate("selected=example('C3').claim_id; setPage('explorer')")
        await capture('02_condition_example')
        # Exercise every condition and the split/source text controls.
        for condition in range(11):
            await evaluate(f"document.querySelector('#condition').value='C{condition}';document.querySelector('#condition').dispatchEvent(new Event('input'))")
            await settle()
        await evaluate("document.querySelector('#split').value='test';document.querySelector('#split').dispatchEvent(new Event('input'))")
        await settle()
        assert await evaluate("document.querySelector('#sample').innerText.includes('test')")
        await evaluate("document.querySelector('#search').value='NONEXISTENT';document.querySelector('#search').dispatchEvent(new Event('input'))")
        assert await evaluate("document.querySelector('#sample').innerText==='Sin coincidencias'")
        for page, name in [('packet','03_evidencepacket_graph'),('leakage','04_leakage_audit'),('repro','05_test_reproducibility'),('tests','06_test_dashboard')]:
            await evaluate(f"setPage('{page}')"); await capture(name)
        await evaluate("document.querySelector('#present').click()")
        for step in range(13):
            await settle()
            assert await evaluate(f"document.querySelector('#step').innerText.startsWith('{step+1} / 13')")
            assert await evaluate("getComputedStyle(document.querySelector('#tour')).display==='none'")
            assert await evaluate("getComputedStyle(document.querySelector('#present')).display==='none'")
            if step < 12: await evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight'}))")
        assert not errors, errors
        print('PASS 10 pages, C0–C10, split/search filters, 13 presentation steps, images, no JS exceptions')
        (HERE / 'generated/browser-check.json').write_text(json.dumps({'result':'PASS','pages':10,'conditions':11,'presentation_steps':13,'js_errors':errors},indent=2))


if __name__ == '__main__':
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome: raise SystemExit('Chrome/Chromium not installed; capture manually per screenshots/README.md')
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='uafeg-browser-') as profile:
        with (HERE / 'generated/chrome.log').open('w') as log:
            process = subprocess.Popen([chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',
                '--remote-debugging-port=9226',f'--user-data-dir={profile}','about:blank'],stdout=log,stderr=log)
            try:
                for _ in range(60):
                    try:
                        urlopen('http://127.0.0.1:9226/json',timeout=1); break
                    except OSError: time.sleep(.1)
                asyncio.run(inspect('http://127.0.0.1:8765/'))
            finally:
                process.terminate(); process.wait(timeout=10)
