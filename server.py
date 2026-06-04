import os
import click
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from config import config
from memory_engine import MemoryEngine
from model import OpenSawLM, AVAILABLE_MODELS

app = FastAPI(title="OpenSaw AI", version="1.0.0")

memory = MemoryEngine(workspace_dir=config.workspace_dir)
lm: Optional[OpenSawLM] = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenSaw AI</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:'SF Mono','Fira Code','Cascadia Code',monospace;height:100vh;display:flex;flex-direction:column}}
#chat{{flex:1;overflow-y:auto;padding:1.5rem;display:flex;flex-direction:column;gap:1rem}}
.msg{{max-width:80%;padding:0.75rem 1rem;border-radius:8px;line-height:1.5;white-space:pre-wrap;word-break:break-word}}
.user{{background:#1f6feb;align-self:flex-end;color:#fff}}
.assistant{{background:#161b22;border:1px solid #30363d;align-self:flex-start;color:#c9d1d9}}
.system{{background:#0d1117;color:#8b949e;text-align:center;font-size:0.85rem;padding:0.5rem}}
#input-area{{display:flex;gap:0;border-top:1px solid #30363d;padding:0.75rem;background:#0d1117}}
#input{{flex:1;background:#161b22;border:1px solid #30363d;border-radius:6px 0 0 6px;padding:0.75rem 1rem;color:#c9d1d9;font-family:inherit;font-size:0.95rem;outline:none}}
#input:focus{{border-color:#1f6feb}}
#send{{background:#238636;border:none;border-radius:0 6px 6px 0;padding:0 1.5rem;color:#fff;font-family:inherit;font-size:0.95rem;cursor:pointer;font-weight:600}}
#send:hover{{background:#2ea043}}
#send:disabled{{background:#484f58;cursor:not-allowed}}
.status{{color:#8b949e;font-size:0.85rem;text-align:center;padding:0.25rem}}
</style>
</head>
<body>
<div id="chat"><div class="system">OpenSaw AI — Local intelligence, zero clouds</div></div>
<div id="input-area"><input id="input" type="text" placeholder="Message OpenSaw..." autofocus><button id="send">Send</button></div>
<div class="status" id="status"></div>
<script>
const chat=document.getElementById('chat'),input=document.getElementById('input'),send=document.getElementById('send'),status=document.getElementById('status');
function addMsg(role,text){const div=document.createElement('div');div.className='msg '+(role==='user'?'user':'assistant');div.textContent=text;chat.appendChild(div);chat.scrollTop=chat.scrollHeight}
async function submit(){const msg=input.value.trim();if(!msg)return;input.value='';send.disabled=true;status.textContent='OpenSaw is thinking...';addMsg('user',msg);try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});const d=await r.json();addMsg('assistant',d.response);status.textContent=d.tokens+' tokens'}catch(e){addMsg('assistant','Error: '+e.message);status.textContent='Error'}finally{send.disabled=false;input.focus()}}
send.addEventListener('click',submit);
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit()}});
</script>
</body>
</html>"""


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    tokens: int


@app.on_event("startup")
async def startup():
    global memory
    memory = MemoryEngine(workspace_dir=config.workspace_dir)


def get_lm() -> OpenSawLM:
    global lm
    if lm is None:
        lm = OpenSawLM(
            model_name=config.model_name,
            device=config.device,
            max_new_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        lm.load(cache_dir=config.datasets_cache)
    return lm


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    _lm = get_lm()
    context_results = memory.search(req.message, top_k=3)
    context = "\n\n".join(r["text"] for r in context_results) if context_results else ""
    system_prompt = (
        f"Ты {config.ai_name}, локальный ИИ-помощник. "
        f"Отвечай естественно, кратко и по делу."
    )
    if context:
        system_prompt += f"\n\nКонтекст из памяти:\n{context}"
    response = _lm.chat(system_prompt, req.message)
    memory.log_conversation(req.message, response)
    tokens = len(response.split())
    return ChatResponse(response=response, tokens=tokens)


@app.get("/api/memory")
async def get_memory():
    return memory.get_memory_stats()


@app.post("/api/forget")
async def forget():
    memory.clear_memory()
    return {"status": "ok", "message": "Memory cleared"}


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": memory.list_sessions()}


@app.get("/api/models")
async def list_models():
    models = []
    for alias, hf_name in AVAILABLE_MODELS.items():
        models.append({"alias": alias, "name": hf_name})
    return {"models": models}


def start_server(host: str = "127.0.0.1", port: int = 8080):
    uvicorn.run(app, host=host, port=port)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=8080, help="Port to bind", type=int)
def serve(host: str, port: int):
    """Start the OpenSaw API server."""
    start_server(host=host, port=port)


if __name__ == "__main__":
    cli()
