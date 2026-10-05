import json, os, platform, shutil, subprocess, threading, time, tkinter as tk
from tkinter import filedialog, messagebox

ROOT=os.path.expanduser("~/.kclone")
CONFIG=os.path.join(ROOT,"config.json")
BG="#07080a"; PANEL="#0d1015"; PANEL2="#11151c"; PANEL3="#161b24"; FG="#f4f7fb"; MUTED="#7f8998"; BLUE="#5ea2ff"; BLUE2="#8cc4ff"; GREEN="#55d69a"; RED="#ff6b7a"; BORDER="#202735"

DEFAULT={"workspace":os.path.join(os.path.expanduser("~"),"KcloneProjects"),"vm":{"memory_mb":6144,"cpus":6,"disk_gb":48,"enable_3d":True},"ai":{"config":".kclone/ai/config.json"}}
os.makedirs(ROOT,exist_ok=True)

def load_config():
    try:
        with open(CONFIG,encoding="utf-8") as f: data=json.load(f)
    except Exception: data={}
    return {**DEFAULT,**data,"vm":{**DEFAULT["vm"],**data.get("vm",{})},"ai":{**DEFAULT["ai"],**data.get("ai",{})}}

def save_config(data):
    with open(CONFIG,"w",encoding="utf-8") as f: json.dump(data,f,indent=2)

def safe_name(name):
    return bool(name) and name not in (".","..") and not any(c in name for c in '/\\:*?"<>|')

class GlowButton(tk.Canvas):
    def __init__(self,parent,text,command,accent=False,width=150,**kw):
        super().__init__(parent,width=width,height=42,bg=kw.pop("bg",PANEL),highlightthickness=0,bd=0)
        self.text=text; self.command=command; self.accent=accent; self.hover=False; self.offset=0
        self.bind("<Enter>",self.enter); self.bind("<Leave>",self.leave); self.bind("<Button-1>",lambda e:self.command())
        self.draw()
    def draw(self):
        self.delete("all"); w=int(self["width"]); h=42
        fill="#1b4f91" if self.accent else PANEL2
        if self.hover: fill="#2868b6" if self.accent else "#1d2531"
        self.create_rectangle(2,2,w-2,h-2,fill=fill,outline="#31577f" if self.hover else BORDER,width=1)
        self.create_text(w//2,21,text=self.text,fill="#ffffff" if self.accent else FG,font=("Segoe UI",10,"bold"))
    def enter(self):
        self.hover=True; self.draw()
    def leave(self):
        self.hover=False; self.draw()

class Kclone(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kclone")
        self.geometry("1500x920"); self.minsize(1180,720); self.configure(bg=BG)
        self.cfg=load_config(); self.workspace=self.cfg["workspace"]; os.makedirs(self.workspace,exist_ok=True)
        self.project=None; self.current_file=None; self.vm_proc=None
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.build_shell(); self.refresh_projects()

    def label(self,p,text,size=10,color=FG,bold=False):
        return tk.Label(p,text=text,bg=p.cget("bg"),fg=color,font=("Segoe UI",size,"bold" if bold else "normal"))

    def build_shell(self):
        top=tk.Frame(self,bg=BG,height=70); top.pack(fill="x",padx=22,pady=(16,8))
        self.label(top,"KCLONE",26,FG,True).pack(side="left")
        self.label(top,"  DEVELOPMENT WORKSPACE",10,MUTED,True).pack(side="left",pady=11)
        right=tk.Frame(top,bg=BG); right.pack(side="right")
        GlowButton(right,"Settings",self.settings,width=120).pack(side="left",padx=4)
        GlowButton(right,"New Project",self.new_project,True,width=145).pack(side="left",padx=4)

        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True,padx=18)
        self.sidebar=tk.Frame(body,bg=PANEL,width=255,highlightbackground=BORDER,highlightthickness=1); self.sidebar.pack(side="left",fill="y",padx=(0,10))
        self.main=tk.Frame(body,bg=BG); self.main.pack(side="left",fill="both",expand=True)
        self.inspector=tk.Frame(body,bg=PANEL,width=300,highlightbackground=BORDER,highlightthickness=1); self.inspector.pack(side="right",fill="y",padx=(10,0))

        self.label(self.sidebar,"WORKSPACE",9,MUTED,True).pack(anchor="w",padx=16,pady=(18,8))
        self.projects=tk.Listbox(self.sidebar,bg=PANEL,fg=FG,selectbackground="#214a78",selectforeground="#fff",relief="flat",bd=0,highlightthickness=0,font=("Segoe UI",10),activestyle="none")
        self.projects.pack(fill="both",expand=True,padx=8); self.projects.bind("<<ListboxSelect>>",lambda e:self.open_selected())
        GlowButton(self.sidebar,"＋  New Project",self.new_project,True,width=220).pack(padx=16,pady=8)
        GlowButton(self.sidebar,"⌂  Workspace",self.choose_workspace,width=220).pack(padx=16,pady=(0,16))

        head=tk.Frame(self.main,bg=BG); head.pack(fill="x",pady=(0,8))
        self.project_title=self.label(head,"No project open",20,FG,True); self.project_title.pack(side="left")
        self.status=self.label(head,"● Ready",9,GREEN,True); self.status.pack(side="right",pady=7)

        split=tk.Frame(self.main,bg=BG); split.pack(fill="both",expand=True)
        explorer=tk.Frame(split,bg=PANEL,highlightbackground=BORDER,highlightthickness=1); explorer.pack(side="left",fill="both",expand=True,padx=(0,6))
        editor=tk.Frame(split,bg="#0a0c10",highlightbackground=BORDER,highlightthickness=1); editor.pack(side="right",fill="both",expand=True,padx=(6,0))
        self.label(explorer,"PROJECT EXPLORER",9,MUTED,True).pack(anchor="w",padx=14,pady=(12,7))
        self.tree=tk.Listbox(explorer,bg=PANEL,fg=FG,selectbackground="#18283b",selectforeground=BLUE2,relief="flat",bd=0,highlightthickness=0,font=("Consolas",10),activestyle="none")
        self.tree.pack(fill="both",expand=True,padx=8,pady=(0,8)); self.tree.bind("<Double-Button-1>",lambda e:self.tree_open())
        self.filebar=tk.Frame(editor,bg=PANEL2,height=40); self.filebar.pack(fill="x")
        self.file_label=self.label(self.filebar,"  Welcome",9,MUTED); self.file_label.pack(side="left",fill="x",expand=True)
        GlowButton(self.filebar,"Save",self.save_file,width=85,bg=PANEL2).pack(side="right",padx=5,pady=4)
        self.editor=tk.Text(editor,bg="#090b0f",fg="#e9edf3",insertbackground=BLUE2,selectbackground="#213c5b",relief="flat",font=("Consolas",11),padx=16,pady=14,undo=True)
        self.editor.pack(fill="both",expand=True)

        self.label(self.inspector,"PROJECT CONTROL",9,MUTED,True).pack(anchor="w",padx=16,pady=(18,8))
        self.card(self.inspector,"AI", "Project-aware AI connection",self.ai_panel)
        self.card(self.inspector,"MCP","Tools, servers and permissions",self.mcp_panel)
        self.card(self.inspector,"RESOURCES","Assets, SDKs and toolchains",self.resources_panel)
        self.card(self.inspector,"VM / OS","Boot, acceleration and testing",self.vm_panel)

        bottom=tk.Frame(self,bg="#050608",height=145,highlightbackground=BORDER,highlightthickness=1); bottom.pack(fill="x",padx=18,pady=(10,16))
        self.label(bottom,"OUTPUT",9,MUTED,True).pack(anchor="w",padx=12,pady=(8,2))
        self.output=tk.Text(bottom,bg="#050608",fg="#9aa5b4",relief="flat",height=6,font=("Consolas",9),state="disabled")
        self.output.pack(fill="both",expand=True,padx=12,pady=(0,7))
        self.log("Kclone ready. Create or open a project.")

    def card(self,parent,title,subtitle,command):
        c=tk.Frame(parent,bg=PANEL2,highlightbackground=BORDER,highlightthickness=1,cursor="hand2")
        c.pack(fill="x",padx=12,pady=5)
        self.label(c,title,10,FG,True).pack(anchor="w",padx=12,pady=(10,1))
        self.label(c,subtitle,8,MUTED).pack(anchor="w",padx=12,pady=(0,9))
        c.bind("<Button-1>",lambda e:command())
        c.bind("<Enter>",lambda e:c.configure(bg=PANEL3))
        c.bind("<Leave>",lambda e:c.configure(bg=PANEL2))

    def log(self,msg):
        self.output.configure(state="normal"); self.output.insert("end",msg+"\n"); self.output.see("end"); self.output.configure(state="disabled")

    def refresh_projects(self):
        self.projects.delete(0,"end")
        for n in sorted(os.listdir(self.workspace)):
            if os.path.isdir(os.path.join(self.workspace,n)) and not n.startswith("."): self.projects.insert("end",n)

    def open_selected(self):
        s=self.projects.curselection()
        if not s:return
        p=os.path.join(self.workspace,self.projects.get(s[0]))
        if os.path.isdir(p): self.open_project(p)

    def open_project(self,p):
        self.project=os.path.abspath(p); self.project_title.config(text=os.path.basename(p)); self.status.config(text="● Project loaded",fg=GREEN); self.populate_tree(); self.log("Opened "+self.project)

    def populate_tree(self):
        self.tree.delete(0,"end")
        if not self.project:return
        def walk(path,depth=0):
            try:names=sorted(os.listdir(path),key=lambda n:(not os.path.isdir(os.path.join(path,n)),n.lower()))
            except OSError:return
            for n in names:
                if n in (".git","__pycache__"):continue
                f=os.path.join(path,n); prefix="   "*depth+("▸ " if os.path.isdir(f) else "• ")
                self.tree.insert("end",prefix+n)
                if os.path.isdir(f):walk(f,depth+1)
        self.tree.insert("end","▾ "+os.path.basename(self.project)); walk(self.project,1)

    def tree_open(self):
        idx=self.tree.curselection()
        if not idx or not self.project:return
        shown=self.tree.get(idx[0]).strip()
        if shown.startswith(("▾ ","▸ ")):return
        rel=shown[2:] if shown.startswith("• ") else shown
        # Resolve displayed relative path by walking from indentation.
        line=self.tree.get(idx[0]); depth=(len(line)-len(line.lstrip(" "))//3)
        rel=shown
        for i in range(idx[0]-1,-1,-1):
            line2=self.tree.get(i); d=(len(line2)-len(line2.lstrip(" ")))//3
            name=line2.strip()
            if d<depth and name.startswith(("▾ ","▸ ")):
                base=name[2:]; rel=os.path.join(base,rel); depth=d; 
                if d==0:break
        path=os.path.join(self.project,rel.replace("\\","/"))
        if os.path.isfile(path):
            try:
                if os.path.getsize(path)>3000000: raise ValueError("File is too large for the editor.")
                with open(path,encoding="utf-8") as f:data=f.read()
                self.current_file=path; self.file_label.config(text="  "+os.path.relpath(path,self.project)); self.editor.delete("1.0","end"); self.editor.insert("1.0",data)
            except Exception as e:self.log(str(e))

    def save_file(self):
        if not self.current_file:return
        try:
            with open(self.current_file,"w",encoding="utf-8") as f:f.write(self.editor.get("1.0","end-1c"))
            self.log("Saved "+self.current_file); self.status.config(text="● Saved",fg=GREEN)
        except Exception as e:messagebox.showerror("Kclone",str(e))

    def new_project(self):
        w=tk.Toplevel(self); w.title("New Project"); w.geometry("620x520"); w.configure(bg=BG); w.transient(self); w.grab_set()
        self.label(w,"Create a new workspace",22,FG,True).pack(anchor="w",padx=32,pady=(28,4))
        self.label(w,"A complete project is created — folders, AI context, MCP, resources and Git.",9,MUTED).pack(anchor="w",padx=32,pady=(0,22))
        form=tk.Frame(w,bg=BG); form.pack(fill="x",padx=32)
        self.label(form,"PROJECT NAME",9,MUTED,True).pack(anchor="w"); name=tk.Entry(form,bg=PANEL2,fg=FG,insertbackground=FG,relief="flat",font=("Segoe UI",12)); name.pack(fill="x",pady=(6,16),ipady=9)
        self.label(form,"TEMPLATE",9,MUTED,True).pack(anchor="w"); template=tk.StringVar(value="OS / ISO")
        for value,desc in [("OS / ISO","Kernel, boot, drivers, assets, resources, artifacts and VM profile"),("Desktop App","Source, assets, resources, build and artifacts"),("Empty","Minimal project with Kclone metadata")]:
            tk.Radiobutton(form,text=value+"   "+desc,variable=template,value=value,bg=BG,fg=FG,selectcolor=PANEL2,activebackground=BG,activeforeground=FG).pack(anchor="w",pady=4)
        error=self.label(w,"",9,RED); error.pack(anchor="w",padx=32,pady=8)
        def create():
            n=name.get().strip()
            if not safe_name(n):error.config(text="Use a valid project name.");return
            p=os.path.join(self.workspace,n)
            if os.path.exists(p):error.config(text="That project already exists.");return
            try:
                os.makedirs(p)
                folders=["src","assets","resources","build","artifacts","docs"] if template.get()!="OS / ISO" else ["kernel","boot","system","drivers","apps","lib","etc","assets/icons","assets/wallpapers","assets/boot","assets/ui","resources","build","scripts","tests","docs","artifacts"]
                for d in folders:os.makedirs(os.path.join(p,d),exist_ok=True)
                k={"name":n,"type":"os" if template.get()=="OS / ISO" else "application","version":4,"ai_project_aware":True,"mcp_project_aware":True,"targets":["iso","exe","apk","aab"],"workspace":{"root":".","asset_tree":"assets","resource_tree":"resources","build_tree":"build","artifact_tree":"artifacts"},"ai":{"config":".kclone/ai/config.json"},"mcp":{"config":".kclone/mcp/servers.json"},"vm":{"memory_mb":6144,"cpus":6,"disk_gb":48,"enable_3d":True}}
                self.write_json(os.path.join(p,"KCLONE.json"),k)
                self.write_json(os.path.join(p,"resources","manifest.json"),{"version":1,"resources":[],"install_root":"resources","auto_include":True})
                self.write_json(os.path.join(p,".kclone","ai","config.json"),{"enabled":True,"provider":"openai-compatible","base_url":"https://api.openai.com/v1","model":"gpt-5","api_key_env":"KCLONE_AI_API_KEY","project_root":".","permissions":{"read":True,"write":True,"delete":True,"build":True,"git":True,"mcp":True,"resources":True,"vm":True}})
                self.write_json(os.path.join(p,".kclone","mcp","servers.json"),{"version":1,"projectAware":True,"scope":"project","mcpServers":{},"capabilities":["workspace","files","assets","resources","build","tests","git","vm"]})
                self.write_json(os.path.join(p,".kclone","vm.json"),{"backend":"qemu","memory_mb":6144,"cpus":6,"disk_gb":48,"graphics":{"device":"virtio-gpu-gl","3d":True,"hostmem":"4G"},"acceleration":{"auto":True,"kvm":True,"whpx":True,"hvf":True}})
                with open(os.path.join(p,".gitignore"),"w",encoding="utf-8") as f:f.write(".venv/\\n__pycache__/\\n*.pyc\\n")
                rr=subprocess.run(["git","init",p],capture_output=True,text=True)
                if rr.returncode:raise RuntimeError(rr.stderr.strip() or "Git initialization failed")
                self.project=p; self.refresh_projects()
                for i in range(self.projects.size()):
                    if self.projects.get(i)==n:self.projects.selection_set(i);break
                self.open_project(p); self.log("Created project successfully."); w.destroy()
            except Exception as e:error.config(text=str(e)); shutil.rmtree(p,ignore_errors=True)
        GlowButton(w,"Create Project",create,True,width=240).pack(pady=18)
        name.focus_set()

    def write_json(self,path,data):
        os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as f:json.dump(data,f,indent=2)

    def ai_panel(self):
        if not self.project:return messagebox.showwarning("AI","Open a project first.")
        p=os.path.join(self.project,".kclone","ai","config.json")
        os.makedirs(os.path.dirname(p),exist_ok=True)
        if not os.path.exists(p):self.write_json(p,{"enabled":True,"provider":"openai-compatible","base_url":"https://api.openai.com/v1","model":"gpt-5","api_key_env":"KCLONE_AI_API_KEY","project_root":"."})
        w=tk.Toplevel(self);w.title("Kclone AI");w.geometry("680x560");w.configure(bg=BG)
        self.label(w,"AI CONNECTION",20,FG,True).pack(anchor="w",padx=28,pady=(25,4));self.label(w,"The connection file now exists inside every project.",9,MUTED).pack(anchor="w",padx=28,pady=(0,18))
        box=tk.Text(w,bg=PANEL,fg=FG,insertbackground=FG,relief="flat",font=("Consolas",10));box.pack(fill="both",expand=True,padx=28);box.insert("1.0",open(p,encoding="utf-8").read())
        def save_ai():
            try:self.write_text(p,box.get("1.0","end-1c"));self.log("AI config saved: "+p);messagebox.showinfo("AI","AI connection configuration saved.")
            except Exception as e:messagebox.showerror("AI",str(e))
        GlowButton(w,"Save AI Configuration",save_ai,True,width=230).pack(pady=14)

    def write_text(self,path,text):
        os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as f:f.write(text)

    def mcp_panel(self):
        if not self.project:return messagebox.showwarning("MCP","Open a project first.")
        p=os.path.join(self.project,".kclone","mcp","servers.json");os.makedirs(os.path.dirname(p),exist_ok=True)
        if not os.path.exists(p):self.write_json(p,{"version":1,"projectAware":True,"scope":"project","mcpServers":{},"capabilities":["workspace","files","assets","resources","build","tests","git","vm"]})
        w=tk.Toplevel(self);w.title("MCP Manager");w.geometry("700x580");w.configure(bg=BG)
        self.label(w,"MCP SERVER MANAGER",20,FG,True).pack(anchor="w",padx=28,pady=(25,4));self.label(w,"Edit the project-scoped JSON used to connect MCP servers.",9,MUTED).pack(anchor="w",padx=28,pady=(0,15))
        box=tk.Text(w,bg=PANEL,fg=FG,insertbackground=FG,relief="flat",font=("Consolas",10));box.pack(fill="both",expand=True,padx=28);box.insert("1.0",open(p,encoding="utf-8").read())
        def save_mcp():
            try:json.loads(box.get("1.0","end-1c"));self.write_text(p,box.get("1.0","end-1c"));self.log("MCP config saved: "+p);messagebox.showinfo("MCP","MCP configuration saved.")
            except Exception as e:messagebox.showerror("MCP","Invalid JSON: "+str(e))
        GlowButton(w,"Save MCP Configuration",save_mcp,True,width=245).pack(pady=14)

    def resources_panel(self):
        if not self.project:return messagebox.showwarning("Resources","Open a project first.")
        r=os.path.join(self.project,"resources");os.makedirs(r,exist_ok=True)
        choice=messagebox.askyesnocancel("Resources","Add a local resource file?\n\nYes = choose file and copy it into resources.\nNo = open resources folder.\nCancel = close.")
        if choice is True:
            f=filedialog.askopenfilename()
            if f:
                shutil.copy2(f,os.path.join(r,os.path.basename(f)));self.log("Installed resource: "+os.path.basename(f));self.populate_tree()
        elif choice is False:
            try:
                if os.name=="nt":os.startfile(r)
                elif platform.system()=="Darwin":subprocess.Popen(["open",r])
                else:subprocess.Popen(["xdg-open",r])
            except Exception:pass

    def find_qemu(self):
        names=["qemu-system-x86_64","qemu-system-x86_64.exe"]
        for n in names:
            p=shutil.which(n)
            if p:return p
        if os.name=="nt":
            for p in [r"C:\Program Files\qemu\qemu-system-x86_64.exe",r"C:\Program Files\QEMU\qemu-system-x86_64.exe",r"C:\ProgramData\chocolatey\bin\qemu-system-x86_64.exe"]:
                if os.path.exists(p):return p
        return None

    def install_qemu(self):
        if os.name=="nt":
            cmd=["winget","install","-e","--id","SoftwareFreedomConservancy.QEMU","--accept-source-agreements","--accept-package-agreements"]
        elif shutil.which("brew"):
            cmd=["brew","install","qemu"]
        elif shutil.which("apt-get"):
            cmd=["sudo","apt-get","update"]
            subprocess.Popen(cmd).wait()
            cmd=["sudo","apt-get","install","-y","qemu-system-x86"]
        else:
            messagebox.showinfo("VM","Install QEMU with your OS package manager, then restart Kclone.");return
        self.log("Installing QEMU...")
        def run():
            try:
                r=subprocess.run(cmd,capture_output=True,text=True)
                self.log(r.stdout[-1500:] if r.stdout else r.stderr[-1500:])
                self.after(0,lambda:messagebox.showinfo("VM","QEMU installation finished. Reopen VM / OS Startup."))
            except Exception as e:self.after(0,lambda:messagebox.showerror("VM",str(e)))
        threading.Thread(target=run,daemon=True).start()

    def vm_panel(self):
        if not self.project:return messagebox.showwarning("VM","Open an OS project first.")
        q=self.find_qemu()
        w=tk.Toplevel(self);w.title("Kclone OS Runtime");w.geometry("700x650");w.configure(bg=BG)
        self.label(w,"OS RUNTIME",22,FG,True).pack(anchor="w",padx=30,pady=(26,4))
        self.label(w,"Boot an ISO with hardware acceleration when the host supports it.",9,MUTED).pack(anchor="w",padx=30,pady=(0,18))
        stat="READY — "+q if q else "QEMU BACKEND NOT INSTALLED"
        self.label(w,stat,9,GREEN if q else RED,True).pack(anchor="w",padx=30,pady=(0,15))
        cfg=tk.Frame(w,bg=PANEL,highlightbackground=BORDER,highlightthickness=1);cfg.pack(fill="x",padx=30)
        values={}
        for title,key,default,hi in [("MEMORY","memory_mb",6144,32768),("CPU CORES","cpus",6,32),("DISK TARGET (GB)","disk_gb",48,512)]:
            row=tk.Frame(cfg,bg=PANEL);row.pack(fill="x",padx=18,pady=8);self.label(row,title,9,MUTED,True).pack(side="left")
            e=tk.Entry(row,bg=PANEL2,fg=FG,insertbackground=FG,relief="flat",width=10);e.insert(0,str(self.cfg["vm"].get(key,default)));e.pack(side="right");values[key]=e
        accel=tk.BooleanVar(value=True);tk.Checkbutton(cfg,text="Enable 3D / VirGL (virtio-gpu-gl)",variable=accel,bg=PANEL,fg=FG,selectcolor=PANEL2,activebackground=PANEL,activeforeground=FG).pack(anchor="w",padx=18,pady=(3,14))
        actions=tk.Frame(w,bg=BG);actions.pack(fill="x",padx=30,pady=18)
        def start():
            q2=self.find_qemu()
            if not q2:
                messagebox.showwarning("QEMU required","Kclone cannot emulate a real OS without a VM backend. Click Install QEMU once; Kclone will set it up automatically where supported.")
                return
            iso=None
            if os.path.isdir(os.path.join(self.project,"artifacts")):
                candidates=[os.path.join(self.project,"artifacts",x) for x in os.listdir(os.path.join(self.project,"artifacts")) if x.lower().endswith(".iso")]
                if candidates:iso=sorted(candidates,key=os.path.getmtime)[-1]
            if not iso:iso=filedialog.askopenfilename(title="Choose bootable ISO",filetypes=[("Bootable ISO","*.iso")],initialdir=os.path.join(self.project,"artifacts"))
            if not iso:return
            mem=int(values["memory_mb"].get()); cpus=int(values["cpus"].get()); disk=int(values["disk_gb"].get())
            self.cfg["vm"]={"memory_mb":mem,"cpus":cpus,"disk_gb":disk,"enable_3d":accel.get()};save_config(self.cfg)
            cmd=[q2,"-accel","auto","-machine","q35","-m",str(mem),"-smp",str(cpus),"-drive",f"file={iso},media=cdrom,readonly=on","-boot","d","-device","virtio-net-pci,netdev=n0","-netdev","user,id=n0","-device","virtio-gpu-gl,hostmem=4G,blob=true"]
            if accel.get():cmd += ["-display","gtk,gl=on" if platform.system()=="Linux" else "sdl,gl=on"]
            else:cmd[-1]="virtio-gpu"
            self.log("Starting accelerated VM: "+" ".join(cmd))
            try:self.vm_proc=subprocess.Popen(cmd);w.destroy()
            except Exception as e:messagebox.showerror("VM",str(e))
        if not q:GlowButton(actions,"Install QEMU",self.install_qemu,True,width=180).pack(side="left",padx=4)
        GlowButton(actions,"Start OS",start,True,width=180).pack(side="left",padx=4)
        GlowButton(actions,"Close",w.destroy,width=120).pack(side="right",padx=4)
        self.label(w,"Recommended guest support: virtio-gpu/DRM in the OS kernel. VirGL 3D depends on host graphics support.",8,MUTED).pack(anchor="w",padx=30,pady=8)

    def choose_workspace(self):
        p=filedialog.askdirectory(initialdir=self.workspace)
        if p:self.workspace=p;self.cfg["workspace"]=p;save_config(self.cfg);self.refresh_projects();self.log("Workspace changed.")

    def settings(self):
        messagebox.showinfo("Kclone","Workspace: "+self.workspace+"\nAI config: per-project .kclone/ai/config.json\nMCP config: per-project .kclone/mcp/servers.json\nVM: QEMU + virtio-gpu-gl/VirGL when available.")

    def close(self):
        try:
            if self.vm_proc and self.vm_proc.poll() is None:self.vm_proc.terminate()
        except Exception:pass
        self.destroy()

if __name__=="__main__": Kclone().mainloop()
