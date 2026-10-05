import json, os, platform, shutil, subprocess, tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP=os.path.join(os.path.expanduser("~"),".kclone"); CFG=os.path.join(APP,"config.json")
BG="#09090b"; PANEL="#111114"; PANEL2="#18181d"; FG="#f4f4f5"; MUTED="#92929d"; SEL="#263b59"
os.makedirs(APP,exist_ok=True)
DEFAULT={"workspace":os.path.join(os.path.expanduser("~"),"KcloneProjects"),"vm":{"memory_mb":4096,"cpus":4,"disk_gb":32,"enable_3d":True}}
def load():
    try:
        with open(CFG,encoding="utf-8") as f: c=json.load(f)
    except Exception: c={}
    return {**DEFAULT,**c,"vm":{**DEFAULT["vm"],**c.get("vm",{})}}
def save(c):
    with open(CFG,"w",encoding="utf-8") as f: json.dump(c,f,indent=2)
def valid(n): return bool(n) and all(x not in n for x in '/\\:*?"<>|') and n not in (".","..")

class Kclone(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Kclone — Development Platform"); self.geometry("1450x900"); self.minsize(1050,680); self.configure(bg=BG)
        self.c=load(); self.workspace=self.c["workspace"]; os.makedirs(self.workspace,exist_ok=True); self.project=None; self.file=None
        self.style(); self.ui(); self.refresh()
    def style(self):
        s=ttk.Style(self); s.theme_use("clam"); s.configure(".",background=BG,foreground=FG,font=("Segoe UI",10))
        s.configure("TFrame",background=BG); s.configure("Panel.TFrame",background=PANEL); s.configure("TLabel",background=BG,foreground=FG)
        s.configure("TButton",background=PANEL2,foreground=FG,borderwidth=0,padding=(12,8)); s.map("TButton",background=[("active","#24242b")])
        s.configure("Accent.TButton",background="#245a9c",foreground="white"); s.map("Accent.TButton",background=[("active","#3274c4")])
        s.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=FG,rowheight=27,borderwidth=0); s.map("Treeview",background=[("selected",SEL)])
    def ui(self):
        h=tk.Frame(self,bg=BG); h.pack(fill="x",padx=18,pady=(14,8))
        tk.Label(h,text="Kclone",bg=BG,fg=FG,font=("Segoe UI",23,"bold")).pack(side="left")
        tk.Label(h,text="  OS • Apps • Build • AI",bg=BG,fg=MUTED).pack(side="left",pady=8)
        for t,cmd,st in [("New Project",self.new_project,"Accent.TButton"),("Open",self.open_folder,"TButton"),("Settings",self.settings,"TButton")]:
            ttk.Button(h,text=t,command=cmd,style=st).pack(side="right",padx=4)
        p=ttk.Panedwindow(self,orient="horizontal"); p.pack(fill="both",expand=True,padx=14,pady=(0,8))
        l=ttk.Frame(p,style="Panel.TFrame",padding=10); m=ttk.Frame(p,style="Panel.TFrame",padding=8); r=ttk.Frame(p,style="Panel.TFrame",padding=10)
        p.add(l,weight=1); p.add(m,weight=4); p.add(r,weight=2)
        ttk.Label(l,text="PROJECTS",foreground=MUTED).pack(anchor="w",pady=(2,8))
        self.projects=tk.Listbox(l,bg=PANEL,fg=FG,selectbackground=SEL,selectforeground=FG,relief="flat",highlightthickness=0,activestyle="none")
        self.projects.pack(fill="both",expand=True); self.projects.bind("<<ListboxSelect>>",lambda e:self.open_selected())
        ttk.Button(l,text="+ New Project",command=self.new_project,style="Accent.TButton").pack(fill="x",pady=8); ttk.Button(l,text="Workspace",command=self.choose_workspace).pack(fill="x")
        ttk.Label(m,text="EXPLORER",foreground=MUTED).pack(anchor="w",pady=(2,6)); self.tree=ttk.Treeview(m,show="tree"); self.tree.pack(fill="both",expand=True); self.tree.bind("<<TreeviewSelect>>",self.tree_file)
        bar=tk.Frame(m,bg=PANEL2); bar.pack(fill="x",pady=(8,0)); self.file_label=tk.Label(bar,text="No file open",bg=PANEL2,fg=MUTED,anchor="w"); self.file_label.pack(side="left",fill="x",expand=True,padx=10,pady=6); ttk.Button(bar,text="Save",command=self.save_file).pack(side="right",padx=4,pady=3)
        self.editor=tk.Text(m,bg="#0d0d10",fg=FG,insertbackground=FG,selectbackground=SEL,relief="flat",undo=True,font=("Consolas",11),padx=12,pady=10); self.editor.pack(fill="both",expand=True)
        ttk.Label(r,text="AI / MCP",foreground=MUTED).pack(anchor="w",pady=(2,6))
        self.ai=tk.Text(r,bg="#0d0d10",fg=FG,relief="flat",wrap="word"); self.ai.pack(fill="both",expand=True); self.ai.insert("end","Kclone project-aware AI\\n\\nWorkspace: files • assets • resources • builds • Git • MCP • VM\\n"); self.ai.configure(state="disabled")
        row=ttk.Frame(r); row.pack(fill="x",pady=8); self.aiin=ttk.Entry(row); self.aiin.pack(side="left",fill="x",expand=True); self.aiin.bind("<Return>",lambda e:self.send_ai()); ttk.Button(row,text="Send",command=self.send_ai,style="Accent.TButton").pack(side="right",padx=(5,0))
        for t,cmd,st in [("MCP Configuration",self.mcp,"TButton"),("Resources",self.resources,"TButton"),("VM / OS Startup",self.vm,"Accent.TButton")]: ttk.Button(r,text=t,command=cmd,style=st).pack(fill="x",pady=2)
        self.out=tk.Text(self,bg="#070708",fg="#b9b9c4",height=7,relief="flat",font=("Consolas",9)); self.out.pack(fill="x",padx=14,pady=(0,14)); self.log("Ready — dark IDE loaded.")
    def log(self,x): self.out.insert("end",x+"\\n"); self.out.see("end")
    def refresh(self):
        self.projects.delete(0,"end")
        for n in sorted(os.listdir(self.workspace)):
            if os.path.isdir(os.path.join(self.workspace,n)) and not n.startswith("."): self.projects.insert("end",n)
    def path(self): 
        s=self.projects.curselection()
        return os.path.join(self.workspace,self.projects.get(s[0])) if s else self.project
    def open_selected(self):
        p=self.path()
        if p and os.path.isdir(p): self.project=os.path.abspath(p); self.populate(); self.log("Opened "+self.project)
    def populate(self):
        self.tree.delete(*self.tree.get_children())
        if not self.project:return
        q=self.tree.insert("", "end",text=os.path.basename(self.project),values=(self.project,"dir"),open=True); self.walk(q,self.project)
    def walk(self,parent,path):
        try: names=sorted(os.listdir(path),key=lambda n:(not os.path.isdir(os.path.join(path,n)),n.lower()))
        except OSError:return
        for n in names:
            if n==".git" or n.startswith("__pycache__"):continue
            f=os.path.join(path,n); k="dir" if os.path.isdir(f) else "file"; q=self.tree.insert(parent,"end",text=n,values=(f,k),open=False)
            if k=="dir":self.walk(q,f)
    def tree_file(self,e=None):
        s=self.tree.selection()
        if not s:return
        v=self.tree.item(s[0],"values")
        if len(v)<2 or v[1]!="file":return
        f=v[0]
        try:
            if os.path.getsize(f)>2000000:return
            with open(f,encoding="utf-8") as z:d=z.read()
        except Exception:return
        self.file=f; self.file_label.config(text=os.path.relpath(f,self.project)); self.editor.delete("1.0","end"); self.editor.insert("1.0",d)
    def save_file(self):
        if not self.file:return
        try:
            with open(self.file,"w",encoding="utf-8") as f:f.write(self.editor.get("1.0","end-1c"))
            self.log("Saved "+self.file)
        except Exception as e:messagebox.showerror("Kclone",str(e))
    def new_project(self):
        w=tk.Toplevel(self); w.title("New Project"); w.geometry("520x350"); w.configure(bg=BG); w.grab_set()
        tk.Label(w,text="Create a project",bg=BG,fg=FG,font=("Segoe UI",18,"bold")).pack(anchor="w",padx=25,pady=(22,5)); tk.Label(w,text="Creates the project, folders, manifest, resources and Git repository.",bg=BG,fg=MUTED).pack(anchor="w",padx=25,pady=(0,15))
        f=ttk.Frame(w); f.pack(fill="x",padx=25); ttk.Label(f,text="Name").pack(anchor="w"); n=ttk.Entry(f); n.pack(fill="x",pady=(3,10)); ttk.Label(f,text="Template").pack(anchor="w")
        typ=ttk.Combobox(f,state="readonly",values=["OS / ISO","Desktop App","Empty"]); typ.current(0); typ.pack(fill="x",pady=(3,10)); priv=tk.BooleanVar(value=True); ttk.Checkbutton(f,text="Private project metadata",variable=priv).pack(anchor="w")
        err=tk.Label(w,text="",bg=BG,fg="#e88"); err.pack(anchor="w",padx=25,pady=4)
        def create():
            name=n.get().strip(); p=os.path.join(self.workspace,name)
            if not valid(name):err.config(text="Invalid project name.");return
            if os.path.exists(p):err.config(text="Project already exists.");return
            try:
                os.makedirs(p)
                dirs=["kernel","boot","system","drivers","apps","lib","etc","assets/icons","assets/wallpapers","assets/boot","assets/ui","resources","build","scripts","tests","docs","artifacts"] if typ.get()=="OS / ISO" else ["src","assets","resources","build","artifacts","docs"]
                for d in dirs:os.makedirs(os.path.join(p,d),exist_ok=True)
                with open(os.path.join(p,"KCLONE.json"),"w",encoding="utf-8") as z:json.dump({"name":name,"type":"os" if typ.get()=="OS / ISO" else "application","version":3,"private":priv.get(),"ai_project_aware":True,"mcp_project_aware":True,"targets":["iso","exe","apk","aab"],"workspace":{"asset_tree":"assets","resource_tree":"resources","build_tree":"build","artifact_tree":"artifacts"},"vm":DEFAULT["vm"]},z,indent=2)
                with open(os.path.join(p,"resources","manifest.json"),"w",encoding="utf-8") as z:json.dump({"resources":[],"install_root":"resources","auto_include":True},z,indent=2)
                os.makedirs(os.path.join(p,".kclone","mcp"),exist_ok=True)
                with open(os.path.join(p,".kclone","mcp","servers.json"),"w",encoding="utf-8") as z:json.dump({"projectAware":True,"mcpServers":{},"scope":"project","capabilities":["workspace","files","assets","resources","build","tests","git","vm"]},z,indent=2)
                rr=subprocess.run(["git","init",p],capture_output=True,text=True)
                if rr.returncode:raise RuntimeError(rr.stderr.strip() or "git init failed")
                self.project=p; self.refresh(); 
                for i in range(self.projects.size()):
                    if self.projects.get(i)==name:self.projects.selection_set(i);break
                self.populate();self.log("Created "+p);w.destroy();messagebox.showinfo("Kclone","Project created successfully.\\n\\n"+p)
            except Exception as e:
                err.config(text=str(e)); shutil.rmtree(p,ignore_errors=True)
        ttk.Button(w,text="Create Project",command=create,style="Accent.TButton").pack(pady=15)
    def choose_workspace(self):
        p=filedialog.askdirectory(initialdir=self.workspace)
        if p:self.workspace=p;self.c["workspace"]=p;save(self.c);self.refresh()
    def open_folder(self):
        p=self.path() or filedialog.askdirectory(initialdir=self.workspace)
        if not p:return
        self.project=os.path.abspath(p);self.populate()
        try:
            if os.name=="nt":os.startfile(p)
            elif platform.system()=="Darwin":subprocess.Popen(["open",p])
            else:subprocess.Popen(["xdg-open",p])
        except Exception:pass
    def send_ai(self):
        x=self.aiin.get().strip()
        if not x:return
        self.aiin.delete(0,"end");self.ai.configure(state="normal");self.ai.insert("end","\\nYou: "+x+"\\n")
        self.ai.insert("end","Context: "+(self.project or "no project")+"\\nAI/MCP is project-scoped; connect an MCP provider to execute file/build/Git actions.\\n");self.ai.configure(state="disabled")
    def mcp(self):
        if not self.project:return messagebox.showwarning("MCP","Open a project first.")
        p=os.path.join(self.project,".kclone","mcp","servers.json");os.makedirs(os.path.dirname(p),exist_ok=True)
        if not os.path.exists(p):
            with open(p,"w",encoding="utf-8") as f:json.dump({"projectAware":True,"mcpServers":{},"scope":"project"},f,indent=2)
        messagebox.showinfo("MCP","Project-aware MCP config ready:\\n"+p)
    def resources(self):
        if not self.project:return messagebox.showwarning("Resources","Open a project first.")
        p=os.path.join(self.project,"resources");os.makedirs(p,exist_ok=True)
        messagebox.showinfo("Resources","Resource root ready:\\n"+p+"\\n\\nInstall SDKs, compilers, fonts, libraries and build assets here. The manifest keeps builds reproducible.")
    def vm(self):
        if not self.project:return messagebox.showwarning("VM","Open an OS project first.")
        w=tk.Toplevel(self);w.title("VM / OS Startup");w.geometry("560x460");w.configure(bg=BG)
        tk.Label(w,text="OS Virtual Machine",bg=BG,fg=FG,font=("Segoe UI",18,"bold")).pack(anchor="w",padx=25,pady=(22,5))
        tk.Label(w,text="QEMU profile: 4 CPU / 4 GB RAM / 32 GB disk, virtio graphics and optional VirGL 3D.",bg=BG,fg=MUTED,wraplength=500,justify="left").pack(anchor="w",padx=25,pady=(0,15))
        form=ttk.Frame(w);form.pack(fill="x",padx=25);vs={}
        for label,key,default,hi in [("RAM (MB)","memory_mb",4096,32768),("CPU cores","cpus",4,32),("Disk (GB)","disk_gb",32,512)]:
            ttk.Label(form,text=label).pack(anchor="w");v=tk.IntVar(value=int(self.c["vm"].get(key,default)));vs[key]=v;ttk.Spinbox(form,from_=1,to=hi,textvariable=v).pack(fill="x",pady=(2,8))
        a=tk.BooleanVar(value=True);ttk.Checkbutton(form,text="Enable 3D acceleration (virtio-gpu / VirGL when supported)",variable=a).pack(anchor="w")
        q=shutil.which("qemu-system-x86_64");tk.Label(w,text=("QEMU: "+q) if q else "QEMU not found — install QEMU and restart Kclone.",bg=BG,fg="#8fd694" if q else "#e88",wraplength=500,justify="left").pack(anchor="w",padx=25,pady=12)
        def start():
            if not q:return messagebox.showerror("VM","QEMU is not installed or not on PATH.")
            iso=filedialog.askopenfilename(title="Select bootable ISO",initialdir=os.path.join(self.project,"artifacts"),filetypes=[("ISO","*.iso"),("All files","*.*")])
            if not iso:return
            self.c["vm"]={"memory_mb":vs["memory_mb"].get(),"cpus":vs["cpus"].get(),"disk_gb":vs["disk_gb"].get(),"enable_3d":a.get()};save(self.c)
            cmd=[q,"-m",str(vs["memory_mb"].get()),"-smp",str(vs["cpus"].get()),"-drive",f"file={iso},media=cdrom,readonly=on","-boot","d","-device","virtio-vga"]
            if a.get():cmd+=["-display","gtk,gl=on" if platform.system()=="Linux" else "sdl,gl=on"]
            self.log("VM: "+" ".join(cmd))
            try:subprocess.Popen(cmd);w.destroy()
            except Exception as e:messagebox.showerror("VM",str(e))
        ttk.Button(w,text="Start VM",command=start,style="Accent.TButton").pack(fill="x",padx=25,pady=8);ttk.Button(w,text="Close",command=w.destroy).pack(fill="x",padx=25)
    def settings(self):messagebox.showinfo("Settings","Dark UI enabled.\\nWorkspace: "+self.workspace+"\\nVM default: 4 CPU / 4 GB RAM / 32 GB disk / 3D enabled.")
if __name__=="__main__":Kclone().mainloop()
