#!/usr/bin/env python3
import argparse, json, os, shutil, subprocess, sys, platform, time

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
      {"name":"project.inspect","description":"Inspect Kclone project metadata, important directories and build configuration.","inputSchema":{"type":"object","properties":{}}},
      {"name":"workspace.list","description":"List project files and folders.","inputSchema":{"type":"object","properties":{"path":{"type":"string","default":"."}}}},
      {"name":"workspace.read_file","description":"Read a UTF-8 project file.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.write_file","description":"Create or replace a UTF-8 project file.","inputSchema":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}},
      {"name":"workspace.make_dir","description":"Create a project directory.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.delete_path","description":"Delete a project file or directory.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
      {"name":"workspace.copy_path","description":"Copy a project path.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}},
      {"name":"workspace.move_path","description":"Move a project path.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}},
      {"name":"assets.list","description":"List files in assets/.","inputSchema":{"type":"object","properties":{}}},
      {"name":"resources.list","description":"Read resources/manifest.json and installed resources.","inputSchema":{"type":"object","properties":{}}},
      {"name":"resources.register","description":"Register a resource in resources/manifest.json.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"path":{"type":"string"},"kind":{"type":"string"},"source":{"type":"string"}},"required":["name","path"]}},
      {"name":"resources.copy","description":"Copy a resource file already inside the project into resources/.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}},
      {"name":"build.validate","description":"Validate the minimum OS/ISO project tree and required build files.","inputSchema":{"type":"object","properties":{}}},
      {"name":"build.run","description":"Run build/build.py in the project.","inputSchema":{"type":"object","properties":{}}},
      {"name":"artifacts.list","description":"List project artifacts.","inputSchema":{"type":"object","properties":{}}},
      {"name":"vm.find_qemu","description":"Detect QEMU on the host and report accelerator/device support.","inputSchema":{"type":"object","properties":{}}},
      {"name":"vm.create_disk","description":"Create a persistent qcow2 VM disk in artifacts/.","inputSchema":{"type":"object","properties":{"size_gb":{"type":"integer","minimum":4}},"required":["size_gb"]}},
      {"name":"git.status","description":"Read local Git status and current branch.","inputSchema":{"type":"object","properties":{}}},
      {"name":"git.commit","description":"Stage all project changes and create a local Git commit.","inputSchema":{"type":"object","properties":{"message":{"type":"string"}},"required":["message"]}}
    ]

def call(name,a):
    if name=="project.inspect":
        meta={}
        for rel in ["KCLONE.json","build/build.json","resources/manifest.json",".kclone/ai/config.json",".kclone/mcp/servers.json",".kclone/vm.json"]:
            p=safe(rel)
            if os.path.isfile(p):
                try:
                    with open(p,encoding="utf-8") as f: meta[rel]=json.load(f)
                except Exception: meta[rel]="unreadable"
        return {"root":root(),"platform":platform.platform(),"metadata":meta}
    if name=="workspace.list":
        p=safe(a.get("path","."))
        return [{"name":n,"type":"directory" if os.path.isdir(os.path.join(p,n)) else "file","path":os.path.relpath(os.path.join(p,n),root()).replace("\\","/")} for n in sorted(os.listdir(p)) if n not in [".git","__pycache__"]]
    if name=="workspace.read_file":
        with open(safe(a["path"]),encoding="utf-8") as f:return f.read()
    if name=="workspace.write_file":
        p=safe(a["path"]);os.makedirs(os.path.dirname(p),exist_ok=True)
        with open(p,"w",encoding="utf-8") as f:f.write(a.get("content",""))
        return {"ok":True,"path":a["path"]}
    if name=="workspace.make_dir":
        os.makedirs(safe(a["path"]),exist_ok=True);return {"ok":True}
    if name=="workspace.delete_path":
        p=safe(a["path"])
        if p==root():raise ValueError("Cannot delete project root")
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p);return {"ok":True}
    if name=="workspace.copy_path":
        s,d=safe(a["source"]),safe(a["destination"]);os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.copytree(s,d,dirs_exist_ok=True) if os.path.isdir(s) else shutil.copy2(s,d);return {"ok":True}
    if name=="workspace.move_path":
        s,d=safe(a["source"]),safe(a["destination"]);os.makedirs(os.path.dirname(d),exist_ok=True);shutil.move(s,d);return {"ok":True}
    if name=="assets.list":
        p=safe("assets");os.makedirs(p,exist_ok=True)
        return [{"path":os.path.relpath(os.path.join(p,n),root()).replace("\\","/"),"type":"directory" if os.path.isdir(os.path.join(p,n)) else "file"} for n in sorted(os.listdir(p))]
    if name=="resources.list":
        p=safe("resources/manifest.json")
        if os.path.isfile(p):
            with open(p,encoding="utf-8") as f: manifest=json.load(f)
        else: manifest={"version":1,"resources":[],"install_root":"resources","auto_include":True}
        return manifest
    if name=="resources.register":
        mp=safe("resources/manifest.json");os.makedirs(os.path.dirname(mp),exist_ok=True)
        try:
            with open(mp,encoding="utf-8") as f: manifest=json.load(f)
        except Exception: manifest={"version":1,"resources":[],"install_root":"resources","auto_include":True}
        item={"name":a["name"],"path":a["path"],"kind":a.get("kind","resource"),"source":a.get("source","local")}
        manifest.setdefault("resources",[]).append(item)
        with open(mp,"w",encoding="utf-8") as f:json.dump(manifest,f,indent=2)
        return {"ok":True,"resource":item}
    if name=="resources.copy":
        src=safe(a["source"]);dest_rel=os.path.join("resources",a.get("destination") or os.path.basename(src))
        dest=safe(dest_rel);os.makedirs(os.path.dirname(dest),exist_ok=True);shutil.copy2(src,dest)
        return {"ok":True,"path":os.path.relpath(dest,root()).replace("\\","/")}
    if name=="build.validate":
        required=["KCLONE.json","resources","build","artifacts"]
        issues=[x for x in required if not os.path.exists(safe(x))]
        if not os.path.isfile(safe("build/build.py")):issues.append("build/build.py")
        return {"valid":not issues,"issues":issues}
    if name=="build.run":
        script=safe("build/build.py")
        if not os.path.isfile(script):return {"ok":False,"error":"build/build.py is missing"}
        p=subprocess.run([sys.executable,script],cwd=root(),capture_output=True,text=True,timeout=1800)
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]}
    if name=="artifacts.list":
        p=safe("artifacts");os.makedirs(p,exist_ok=True)
        return [{"name":n,"size":os.path.getsize(os.path.join(p,n)) if os.path.isfile(os.path.join(p,n)) else None} for n in sorted(os.listdir(p))]
    if name=="vm.find_qemu":
        for n in ["qemu-system-x86_64","qemu-system-x86_64.exe"]:
            found=shutil.which(n)
            if found:
                accel=subprocess.run([found,"-accel","help"],capture_output=True,text=True).stdout.lower()
                dev=subprocess.run([found,"-device","help"],capture_output=True,text=True).stdout
                return {"installed":True,"path":found,"accelerators":accel.splitlines(),"virtio_gpu_gl":"virtio-gpu-gl" in dev,"platform":platform.system()}
        return {"installed":False,"platform":platform.system()}
    if name=="vm.create_disk":
        size=int(a["size_gb"])
        if size<4:raise ValueError("VM disk must be at least 4 GB")
        qimg=shutil.which("qemu-img")
        if not qimg:return {"ok":False,"error":"qemu-img not found"}
        path=safe("artifacts/vm-disk.qcow2");os.makedirs(os.path.dirname(path),exist_ok=True)
        if os.path.exists(path):return {"ok":True,"existing":True,"path":os.path.relpath(path,root()).replace("\\","/")}
        p=subprocess.run([qimg,"create","-f","qcow2",path,f"{size}G"],capture_output=True,text=True)
        return {"ok":p.returncode==0,"path":os.path.relpath(path,root()).replace("\\","/"),"stdout":p.stdout,"stderr":p.stderr}
    if name=="git.status":
        p=subprocess.run(["git","status","--short","--branch"],cwd=root(),capture_output=True,text=True)
        return {"ok":p.returncode==0,"output":p.stdout or p.stderr}
    if name=="git.commit":
        msg=a["message"].strip()
        if not msg:raise ValueError("Commit message is required")
        add=subprocess.run(["git","add","-A"],cwd=root(),capture_output=True,text=True)
        if add.returncode:return {"ok":False,"error":add.stderr}
        p=subprocess.run(["git","commit","-m",msg],cwd=root(),capture_output=True,text=True)
        return {"ok":p.returncode==0,"output":p.stdout or p.stderr}
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
