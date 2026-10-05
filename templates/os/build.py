import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
META=json.loads((ROOT/"KCLONE.json").read_text(encoding="utf-8"))
NAME=META.get("name","kclone-os")
STAGE=ROOT/"build"/"iso-root"
OUT=ROOT/"artifacts"/(NAME+".iso")

def copy_tree(src,dst):
    if not src.exists(): return
    for p in src.rglob("*"):
        q=dst/p.relative_to(src)
        if p.is_dir(): q.mkdir(parents=True,exist_ok=True)
        else: q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)

def main():
    (ROOT/"artifacts").mkdir(exist_ok=True)
    STAGE.mkdir(parents=True,exist_ok=True)
    for name in ["boot","system","etc","lib","usr","bin","sbin","home","assets"]:
        src=ROOT/name
        if src.exists(): copy_tree(src,STAGE/name)
    rootfs=ROOT/"rootfs"
    if rootfs.exists(): copy_tree(rootfs,STAGE)
    if not (STAGE/"boot").exists():
        raise SystemExit("Missing boot/. Add a bootloader and kernel before building.")
    tool=shutil.which("grub-mkrescue") or shutil.which("xorriso") or shutil.which("mkisofs")
    if not tool:
        raise SystemExit("Install xorriso or grub-mkrescue to build an ISO.")
    OUT.unlink(missing_ok=True)
    base=os.path.basename(tool)
    if base.startswith("grub-mkrescue"):
        cmd=[tool,"-o",str(OUT),str(STAGE)]
    elif base=="xorriso":
        cmd=[tool,"-as","mkisofs","-R","-J","-o",str(OUT),str(STAGE)]
    else:
        cmd=[tool,"-R","-J","-o",str(OUT),str(STAGE)]
    print("Building",OUT)
    raise SystemExit(subprocess.run(cmd,cwd=ROOT).returncode)

if __name__=="__main__":
    main()
