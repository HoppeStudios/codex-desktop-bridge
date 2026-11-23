"""Local policy, storage and background adapter tests. Never touches a real app."""
import asyncio
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import agent_bridge as b
from contextlib import closing, contextmanager

@contextmanager
def fixture_db(path):
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            yield connection

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.p=patch.object(b,'CODEX',self.root); self.p.start()
        self.addCleanup(self.tmp.cleanup); self.addCleanup(self.p.stop)
        self.transcript=self.root/'sessions'/'t.jsonl'
        self.transcript.parent.mkdir()
        self.transcript.write_text(''.join(json.dumps(x)+'\n' for x in [
            {'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'Hello'}]}},
            {'type':'response_item','payload':{'type':'message','role':'assistant','phase':'commentary','content':[{'type':'output_text','text':'Hidden commentary'}]}},
            {'type':'event_msg','payload':{'type':'task_complete','last_agent_message':'Final answer'}}]),encoding='utf8')
        with fixture_db(self.root/'state_5.sqlite') as c:
            c.executescript('CREATE TABLE threads(id TEXT,name TEXT,title TEXT,cwd TEXT,project_id TEXT,updated_at INTEGER,rollout_path TEXT,archived INTEGER,thread_source TEXT);CREATE TABLE projects(id TEXT,name TEXT,position INTEGER);CREATE TABLE project_roots(project_id TEXT,path TEXT,position INTEGER);')
            c.execute('INSERT INTO threads VALUES(?,?,?,?,?,?,?,?,?)',('id1','Example','old','root',None,100,str(self.transcript),0,'user'))
    def test_projectless_metadata_and_limit(self):
        rows=b.codex_list_chats(); self.assertEqual(rows[0]['title'],'Example')
        self.assertNotIn('messages',rows[0])
        for n in (0,-1,101):
            with self.assertRaises(b.ToolError): b.codex_list_chats(limit=n)
    def test_read_only_storage(self):
        before=(self.root/'state_5.sqlite').read_bytes()
        with self.assertRaises(b.ToolError): b.query('state_5.sqlite','DELETE FROM threads')
        self.assertEqual(before,(self.root/'state_5.sqlite').read_bytes())
        self.assertEqual(len(b.codex_list_chats()),1)
    def test_final_messages_and_missing_goal(self):
        reply=b.codex_read_chat('id1')
        self.assertEqual([x['text'] for x in reply['messages']],['Hello','Final answer'])
        self.assertIsNone(reply['goal'])
    def test_ambiguous_titles_refused(self):
        with fixture_db(self.root/'state_5.sqlite') as c:
            c.execute("INSERT INTO threads SELECT 'id2',name,title,cwd,project_id,updated_at,rollout_path,archived,thread_source FROM threads")
        with self.assertRaises(b.ToolError): b.chat_row('Example')
        self.assertEqual(b.chat_row('id1')['id'],'id1')
    def test_escaping_transcript_refused(self):
        with fixture_db(self.root/'state_5.sqlite') as c:
            c.execute('UPDATE threads SET rollout_path=?',(str(self.root.parent/'unrelated.jsonl'),))
        with self.assertRaises(b.ToolError): b.codex_read_chat('id1')
    def test_missing_schema_fails_closed(self):
        with fixture_db(self.root/'state_5.sqlite') as c: c.execute('DROP TABLE threads')
        with self.assertRaises(b.ToolError): b.codex_list_chats()
    def test_app_created_work_chats_included_internal_agents_excluded(self):
        with fixture_db(self.root/'state_5.sqlite') as c:
            c.execute("INSERT INTO threads SELECT 'app',name,title,cwd,project_id,updated_at,rollout_path,archived,'agent_created_thread' FROM threads LIMIT 1")
            c.execute("INSERT INTO threads SELECT 'internal',name,title,cwd,project_id,updated_at,rollout_path,archived,'subagent' FROM threads LIMIT 1")
        self.assertEqual({r['id'] for r in b.codex_list_chats()},{'id1','app'})

class IdentityTests(unittest.TestCase):
    def test_package_identity(self):
        with patch.dict(b.os.environ,{'ProgramFiles':r'C:\Program Files'}):
            self.assertTrue(b.package_path_ok(r'C:\Program Files\WindowsApps\OpenAI.Codex_26.1117.4957.0_x64__2p2nqsd0c76g0\app\ChatGPT.exe'))
            for p in (r'C:\Temp\ChatGPT.exe',r'C:\Program Files\WindowsApps\Other_1_x64__test\app\ChatGPT.exe',r'C:\Program Files\WindowsApps\OpenAI.Codex_1_x64__fake\app\ChatGPT.exe'):
                self.assertFalse(b.package_path_ok(p))
    def test_pin_and_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); exe=root/'pc-control-mcp.exe'; exe.write_bytes(b'fixture')
            cfg={'command':str(exe),'sha256':hashlib.sha256(b'fixture').hexdigest(),'env':{'PC_CONTROL_MODE':'strict','PC_CONTROL_ALLOW':'chatgpt','PC_CONTROL_ISOLATED_DEFAULT':'0'}}
            config=root/'backend.json'; config.write_text(json.dumps(cfg))
            with patch.object(b,'BACKEND_CONFIG',str(config)):
                self.assertEqual(b.backend_settings()['command'],str(exe))
                cfg['env']['PC_CONTROL_MODE']='bypass'; config.write_text(json.dumps(cfg))
                with self.assertRaises(b.ToolError): b.backend_settings()
                cfg['env']['PC_CONTROL_MODE']='strict'; config.write_text(json.dumps(cfg)); exe.write_bytes(b'changed')
                with self.assertRaises(b.ToolError): b.backend_settings()
    def test_no_upstream_takeover_paths(self):
        text=Path(b.__file__).read_text('utf8')
        for forbidden in ('SetForegroundWindow','AttachThreadInput','SetClipboardText','SendKeys','SendInput','_spawn_watch','claude -p'):
            self.assertNotIn(forbidden,text)
    def test_duplicate_and_literal_sidebar_labels(self):
        s='[4:Hello (a)+] (listitem)\n[5:Hello (a)+] (button)'
        self.assertEqual(b.parse_targets(s,'Hello (a)+','listitem'),['4'])

class FakeBackend:
    replies=[]; calls=[]
    async def __aenter__(self): return self
    async def __aexit__(self,*exc): pass
    async def call(self,name,args):
        self.calls.append((name,args)); answer=self.replies.pop(0)
        if isinstance(answer,Exception): raise answer
        return answer

class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.p=patch.object(b,'Backend',FakeBackend); self.p.start(); self.addCleanup(self.p.stop)
        self.v=patch.object(b,'verify_window',return_value={'window':'1'}); self.v.start(); self.addCleanup(self.v.stop)
        FakeBackend.calls=[]
    async def test_sidebar_changed_and_verified_czech(self):
        FakeBackend.replies=['[1:Skrýt postranní panel] (button)','ok (background)', '[2:Zobrazit postranní panel] (button)']
        result=await b.codex_desktop_set_sidebar('1',False)
        self.assertTrue(result['verified']); self.assertTrue(result['changed'])
        self.assertEqual([x[0] for x in FakeBackend.calls],['look','click','look'])
    async def test_noop_never_clicks(self):
        FakeBackend.replies=['[1:Hide sidebar] (button)']
        self.assertFalse((await b.codex_desktop_set_sidebar('1',True))['changed'])
        self.assertEqual(len(FakeBackend.calls),1)
    async def test_backend_refusal_never_retries(self):
        FakeBackend.replies=['[1:Hide sidebar] (button)',b.ToolError('NOT EXECUTED')]
        with self.assertRaises(b.ToolError): await b.codex_desktop_set_sidebar('1',False)
        self.assertEqual(len(FakeBackend.calls),2)
    async def test_failed_readback_not_success(self):
        FakeBackend.replies=['[1:Hide sidebar] (button)','ok but no visible effect','[1:Hide sidebar] (button)']
        result=await b.codex_desktop_set_sidebar('1',False)
        self.assertFalse(result['verified']); self.assertIsNone(result['visible'])
    async def test_select_ambiguous_row_never_clicks(self):
        FakeBackend.replies=['[1:Example] (listitem)\n[2:Example] (listitem)']
        with patch.object(b,'chat_row',return_value={'id':'id1','title':'Example'}),patch.object(b,'threads',return_value=[{'title':'Example'}]):
            with self.assertRaises(b.ToolError): await b.codex_desktop_select_chat('1','id1')
        self.assertEqual([x[0] for x in FakeBackend.calls],['look'])

if __name__=='__main__': unittest.main()
