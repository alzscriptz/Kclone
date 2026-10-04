import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_DIR = os.path.join(os.path.expanduser("~"), ".kclone")
CONFIG = os.path.join(APP_DIR, "config.json")

os.makedirs(APP_DIR, exist_ok=True)

def load_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"workspace": os.path.join(os.path.expanduser("~"), "KcloneProjects")}

def save_config(c):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

class Kclone(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kclone")
        self.geometry("1050x700")
        self.minsize(850, 550)
        self.config_data = load_config()
        self.workspace = self.config_data["workspace"]
        os.makedirs(self.workspace, exist_ok=True)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Kclone", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="New Project", command=self.new_project).pack(side="right")
        ttk.Button(top, text="Workspace", command=self.choose_workspace).pack(side="right", padx=8)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=(0,12))

        left = ttk.Frame(body, padding=8)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Repositories", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.projects = tk.Listbox(left, activestyle="none")
        self.projects.pack(fill="both", expand=True, pady=8)
        self.projects.bind("<<ListboxSelect>>", lambda e: self.open_selected())

        ttk.Label(right, text="Project", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.info = tk.Text(right, wrap="word", state="disabled")
        self.info.pack(fill="both", expand=True, pady=8)

        bottom = ttk.Frame(right)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Open Folder", command=self.open_folder).pack(side="left")
        ttk.Button(bottom, text="Build", command=self.build_project).pack(side="left", padx=8)
        ttk.Button(bottom, text="AI / MCP", command=self.ai_info).pack(side="left")

    def refresh(self):
        self.projects.delete(0, "end")
        for name in sorted(os.listdir(self.workspace)):
            if os.path.isdir(os.path.join(self.workspace, name)):
                self.projects.insert("end", name)

    def selected_path(self):
        sel = self.projects.curselection()
        return os.path.join(self.workspace, self.projects.get(sel[0])) if sel else None

    def open_selected(self):
        p = self.selected_path()
        if not p: return
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("end", f"Repository: {os.path.basename(p)}\n\nPath: {p}\n\nFiles:\n")
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d != ".git"]
            for f in files[:500]:
                self.info.insert("end", os.path.relpath(os.path.join(root, f), p) + "\n")
        self.info.configure(state="disabled")

    def new_project(self):
        win = tk.Toplevel(self)
        win.title("New Kclone Project")
        win.geometry("420x210")
        ttk.Label(win, text="Project name").pack(anchor="w", padx=20, pady=(20,4))
        name = ttk.Entry(win)
        name.pack(fill="x", padx=20)
        private = tk.BooleanVar(value=True)
        ttk.Checkbutton(win, text="Private", variable=private).pack(anchor="w", padx=20, pady=10)
        def create():
            n = name.get().strip()
            if not n or any(c in n for c in '/\\'):
                messagebox.showerror("Kclone", "Enter a valid project name.")
                return
            p = os.path.join(self.workspace, n)
            os.makedirs(p, exist_ok=False)
            with open(os.path.join(p, "KCLONE.json"), "w", encoding="utf-8") as f:
                json.dump({"name": n, "private": private.get(), "version": 1}, f, indent=2)
            subprocess.run(["git", "init", p], capture_output=True, text=True)
            win.destroy()
            self.refresh()
        ttk.Button(win, text="Create", command=create).pack(pady=12)

    def choose_workspace(self):
        p = filedialog.askdirectory(initialdir=self.workspace)
        if p:
            self.workspace = p
            self.config_data["workspace"] = p
            save_config(self.config_data)
            self.refresh()

    def open_folder(self):
        p = self.selected_path()
        if p and os.name == "nt":
            os.startfile(p)

    def build_project(self):
        p = self.selected_path()
        if not p: return
        messagebox.showinfo("Kclone", "Build engine placeholder created. ISO/APK/EXE workers will be added in the next milestone.")

    def ai_info(self):
        messagebox.showinfo("AI / MCP", "AI and MCP configuration is planned for the next milestone.")

if __name__ == "__main__":
    Kclone().mainloop()
