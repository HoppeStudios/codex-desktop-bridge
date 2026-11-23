"""Read-only smoke through the exact registration. Prints counts, never transcripts."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import tomllib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run(cfg):
    async with stdio_client(StdioServerParameters(command=cfg['command'],args=cfg['args'],env=cfg.get('env',{}))) as transport:
        async with ClientSession(*transport) as session:
            hello=await session.initialize()
            listing=await session.list_tools()
            required={'codex_list_projects','codex_list_chats','codex_read_chat','codex_get_goal','codex_desktop_windows','codex_desktop_inspect','codex_desktop_select_chat','codex_desktop_set_sidebar'}
            assert {t.name for t in listing.tools}==required
            async def call(name,args):
                result=await session.call_tool(name,args)
                if result.isError: raise RuntimeError(name+' failed: '+str(result.content)[:1000])
                # FastMCP wraps non-object output as {result: ...} in structuredContent.
                data=result.structuredContent
                if data is not None: return data.get('result',data)
                return json.loads(next(x.text for x in result.content if x.type=='text'))
            projects=await call('codex_list_projects',{})
            chats=await call('codex_list_chats',{'limit':1})
            windows=await call('codex_desktop_windows',{})
            assert windows, 'No verified open Codex app window'
            snapshots=[]
            for window in windows:
                read=await call('codex_desktop_inspect',{'window':window['window'],'find':'sidebar|postranní panel'})
                snapshots.append({'window':window['window'],'chars':len(read['snapshot'])})
            return {'server':hello.serverInfo.name,'version':hello.serverInfo.version,'tools':len(listing.tools),'projects':len(projects),'sample_chats':len(chats),'verified_windows':len(windows),'ui_snapshots':snapshots,'mutations':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--config',type=Path)
    group.add_argument('--registration-json',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    cfg=tomllib.loads(args.config.read_text('utf8'))['mcp_servers']['codex_desktop'] if args.config else json.loads(args.registration_json.read_text('utf8'))
    result=asyncio.run(run(cfg))
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(text+'\n','utf8')
    print(text)
