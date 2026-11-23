"""Stage the reviewed source in an existing dedicated, locked Python venv.
Never changes global settings or replaces a differing runtime payload.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib

parser=argparse.ArgumentParser()
parser.add_argument('--target',type=Path,required=True)
parser.add_argument('--config',type=Path,required=True)
args=parser.parse_args()
source=Path(__file__).resolve().parent.parent
target=args.target.resolve()
python=target/'venv'/'Scripts'/'python.exe'
if not python.is_file(): raise SystemExit('First create a dedicated venv and install requirements.lock.txt with --require-hashes')
config=tomllib.loads(args.config.read_text('utf8'))
backend=config['mcp_servers']['Codex-Window']
required={'PC_CONTROL_MODE':'strict','PC_CONTROL_ALLOW':'chatgpt','PC_CONTROL_ISOLATED_DEFAULT':'0'}
if any(backend['env'].get(k)!=v for k,v in required.items()) or backend.get('args',[]):
    raise SystemExit('Existing Codex-Window registration is not the reviewed strict profile')
command=Path(backend['command']).resolve()
if command.name.casefold()!='pc-control-mcp.exe' or not command.is_file(): raise SystemExit('Pinned Codex-Window launcher missing')
app=target/'app'; app.mkdir(exist_ok=True)
for name in ('agent_bridge.py','transcripts.py','LICENSE','requirements.lock.txt'):
    payload=(source/name).read_bytes()
    dest=app/name
    if dest.exists() and dest.read_bytes()!=payload: raise SystemExit('Refusing to replace a differing installed payload; stage a new version target')
    dest.write_bytes(payload)
backend_cfg={'command':str(command),'args':[], 'env':backend['env'],'sha256':hashlib.sha256(command.read_bytes()).hexdigest()}
(target/'backend.json').write_text(json.dumps(backend_cfg,indent=2)+'\n','utf8')
registration={'command':str(python),'args':['-B',str(app/'agent_bridge.py')],'startup_timeout_sec':120,'tool_timeout_sec':120,'env':{'CODEX_DESKTOP_BACKEND_CONFIG':str(target/'backend.json'),'CODEX_HOME':str(args.config.resolve().parent),'DO_NOT_TRACK':'1','OTEL_SDK_DISABLED':'true','PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1','PYTHONUNBUFFERED':'1'}}
(target/'registration.json').write_text(json.dumps(registration,indent=2)+'\n','utf8')
print('Prepared reviewed stdio installation; global settings unchanged')
