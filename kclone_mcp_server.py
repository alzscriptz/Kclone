#!/usr/bin/env python3
import argparse, json, os, shutil, subprocess, sys

def root():
    return os.path.abspath(os.environ.get("KCLONE_PROJECT_ROOT","."))
def safe(rel):
    base=root(); p=os.path.abspath(os.path.join(base,rel))
    if p!=base and not p.startswith(base+os.sep): raise ValueError("Path escapes project root")
    return p
def reply(req,value=None,error=None):
    out={"jsonrpc":"2.0","id":req.get("id")}
    if error is not None: out["error"]={"code":-32000,"message":str(error)}
    else: out["result"]=value if value is not None else {}
    print(json.dumps(out),flush=True)
def tools():
    return [
      {"name":"workspace.list","description":"List project files and folders.","inputSchema":{"type":"object","properties":{"path":{"type":"string","default":"."}}}},
      {"name":"workspace.read_file","description":"Read a UTF-8 project file.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.write_file","description":"Create or replace a UTF-8 project file.","inputSchema":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}},
      {"name":"workspace.make_dir","description":"Create a project directory.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.delete_path","description":"Delete a project file or directory.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.copy_path","description":"Copy a project path.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}},
      {"name":"workspace.move_path","description":"Move a project path.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}},
      {"name":"build.run","description":"Run build/build.py in the project.","inputSchema":{"type":"object","properties":{}}},
      {"name":"artifacts.list","description":"List project artifacts.","inputSchema":{"type":"object","properties":{}}},
      {"name":"resources.list","description":"Read resources/manifest.json.","inputSchema":{"type":"object","properties":{}}},
      {"name":"vm.find_qemu","description":"Detect QEMU on the host.","inputSchema":{"type":"object","properties":{}}}
    ]
def call(name,a):
    if name=="workspace.list":
        p=safe(a.get("path","."))
        return [{"name":n,"type":"directory" if os.path.isdir(os.path.join(p,n)) else "file","path":os.path.relpath(os.path.join(p,n),root()).replace("\\","/")} for n in sorted(os.listdir(p)) if n!=".git"]
    if name=="workspace.read_file":
        with open(safe(a["path"]),encoding="utf-8") as f:return f.read()
    if name=="workspace.write_file":
        p=safe(a["path"]);os.makedirs(os.path.dirname(p),exist_ok=True)
        with open(p,"w",encoding="utf-8") as f:f.write(a.get("content",""))
        return {"ok":True}
    if name=="workspace.make_dir":
        os.makedirs(safe(a["path"]),exist_ok=True);return {"ok":True}
    if name=="workspace.delete_path":
        p=safe(a["path"]);shutil.rmtree(p) if os.path.isdir(p) else os.remove(p);return {"ok":True}
    if name=="workspace.copy_path":
        s,d=safe(a["source"]),safe(a["destination"]);os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.copytree(s,d,dirs_exist_ok=True) if os.path.isdir(s) else shutil.copy2(s,d);return {"ok":True}
    if name=="workspace.move_path":
        s,d=safe(a["source"]),safe(a["destination"]);os.makedirs(os.path.dirname(d),exist_ok=True);shutil.move(s,d);return {"ok":True}
    if name=="build.run":
        script=safe("build/build.py")
        if not os.path.isfile(script):return {"ok":False,"error":"build/build.py is missing"}
        p=subprocess.run([sys.executable,script],cwd=root(),capture_output=True,text=True,timeout=1800)
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]}
    if name=="artifacts.list":
        p=safe("artifacts");os.makedirs(p,exist_ok=True)
        return [{"name":n,"size":os.path.getsize(os.path.join(p,n)) if os.path.isfile(os.path.join(p,n)) else None} for n in sorted(os.listdir(p))]
    if name=="resources.list":
        p=safe("resources/manifest.json")
        if not os.path.isfile(p):return {"resources":[]}
        with open(p,encoding="utf-8") as f:return json.load(f)
    if name=="vm.find_qemu":
        for n in ["qemu-system-x86_64","qemu-system-x86_64.exe"]:
            found=shutil.which(n)
            if found:return {"installed":True,"path":found}
        return {"installed":False}
    raise ValueError("Unknown tool: "+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root");args=ap.parse_args()
    if args.root:os.environ["KCLONE_PROJECT_ROOT"]=os.path.abspath(args.root)
    for line in sys.stdin:
        try:
            req=json.loads(line);m=req.get("method")
            if m=="initialize":reply(req,{"protocolVersion":"2025-11-25","capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"Kclone Workspace","version":"1.0"}})
            elif m=="notifications/initialized":continue
            elif m=="tools/list":reply(req,{"tools":tools()})
            elif m=="tools/call":
                try:reply(req,{"content":[{"type":"text","text":json.dumps(call(req["params"]["name"],req["params"].get("arguments",{})),indent=2)}]})
                except Exception as e:reply(req,{"content":[{"type":"text","text":str(e)}],"isError":True})
            elif m=="ping":reply(req,{})
            elif "id" in req:reply(req,error="Unsupported method: "+str(m))
        except Exception as e:print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":str(e)}}),flush=True)
if __name__=="__main__":main()
