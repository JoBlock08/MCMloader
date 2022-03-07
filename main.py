from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter.messagebox import askyesno
from tkinter.scrolledtext import ScrolledText
import zipfile
import os
import shutil
import traceback
import requests
import json
import threading

root = Tk()
root.wm_title("MPDWN")

frm = ttk.Frame(root, padding=10)
frm.grid()

modpackZip = ""
modpackRoot = ""

api_url = 'https://addons-ecs.forgesvc.net/api/v2'
files_url = 'https://media.forgecdn.net/files'

def download(url, dest):
        print("Downloading %s" % url)
        r = requests.get(url)
        with open(dest, 'wb') as f:
            f.write(r.content)
        return r.status_code

def get_json(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'})
    if r.status_code != 200:
        if r.status_code == 504:
            return get_json(url)
        print("Error %d trying to access %s" % (r.status_code, url))
        print(r.text)
        return None
    return json.loads(r.text)

downloading = False

def dwn(manifest_json, destination):
    global downloading
    if downloading:    
        progress["value"] = 0
        jars = []
        with open(manifest_json, "r") as f:
            manifest = json.load(f)
        print("Starting Download of " + manifest["name"] + " by " + manifest["author"])
        for f in manifest["files"]:
            if downloading:
                pid = f['projectID']
                fid = f['fileID']
                project_info = get_json(api_url + ('/addon/%d' % pid))
                # print(project_info['websiteUrl'])
                file_type = project_info['websiteUrl'].split('/')[4] # mc-mods or texture-packs
                info = get_json(api_url + ('/addon/%d/file/%d' % (pid, fid)))
                if info is None:
                    return None
                fn = info['fileName']
                dl = info['downloadUrl']
                out_file = destination + '/' + fn
                if os.path.exists(out_file):
                    if os.path.getsize(out_file) == info['fileLength']:
                        print("%s OK" % fn)
                        jars.append(out_file)
                download(dl, out_file)
                jars.append(out_file)
                root.update_idletasks()
                progress['value'] += (500 / len(manifest["files"]))
        downloading = False
    


def askModpackZip():
    global modpackZip
    filetypes = (("Zip Archives" , "*.zip"),)
    modpackZip = fd.askopenfilename(title="Open an Modpack Export", filetypes=filetypes)
    print("ModpackZip: " + modpackZip)

def askModpackRoot():
    global modpackRoot
    modpackRoot = fd.askdirectory()
    print("ModpackRoot: " + modpackRoot)


def DownloadMods(mf, dest):
    try:
        dwn(mf, dest)
    except:
        traceback.print_exc()
        if messagebox.askretrycancel(title="Error", message="An error occured while downloading files."):
            DownloadMods(mf, dest)

def cancelDownload():
    global downloading
    downloading = False
    installbtn.grid(column=0, row=3)
    cancelbtn.grid_forget()


def install():
    if modpackZip == "" or modpackRoot == "":
        messagebox.showerror(title="Error", message="Please select a Modpack root and a Modpack Export")
    else:
        doit = askyesno(title="Install?", message="Are you sure you want to install " + modpackZip.split("/")[-1] + " into " + modpackRoot + " ?")
        if doit:
            installbtn.grid_forget()
            cancelbtn.grid(column=0, row=3)
            os.makedirs(modpackRoot, exist_ok=True)
            os.makedirs(modpackRoot + "/temp", exist_ok=True)
            os.makedirs(modpackRoot + "/mods", exist_ok=True)
            with zipfile.ZipFile(modpackZip, 'r') as zip_ref:
                zip_ref.extractall(modpackRoot + "/temp")
            manifest = modpackRoot + "/temp" + "/manifest.json"
            global downloading
            downloading = True
            DownloadMods(manifest, modpackRoot + "/mods")
            shutil.copytree(modpackRoot + "/temp/overrides", modpackRoot, dirs_exist_ok=True)
            shutil.rmtree(modpackRoot + "/temp")
            print("Done!")
            messagebox.showinfo(title="Done!", message="Done installing Modpack")

x = threading.Thread(target=install)

ttk.Label(frm, text="JoBlocks Modpack installer").grid(column=0, row=0)

ttk.Button(frm, text="Select Modpack Export", command=askModpackZip).grid(column=0, row=1)

ttk.Button(frm, text="Select Modpack Root", command=askModpackRoot).grid(column=0, row=2)

progress = ttk.Progressbar(root, orient=HORIZONTAL, length=500, mode="determinate", maximum=500)
progress.grid(column=0, row=4)


installbtn = ttk.Button(frm, text="Install", command=x.start)
installbtn.grid(column=0, row=3)

cancelbtn = ttk.Button(frm, text="Cancel", command=cancelDownload)
cancelbtn.grid_forget()

ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=5)

root.mainloop()
