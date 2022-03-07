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
import asyncio
from concurrent.futures import ThreadPoolExecutor

root = Tk()
root.wm_title("MPDWN")

frm = ttk.Frame(root, padding=10)
frm.grid()

modpackZip = ""
modpackRoot = ""

api_url = 'https://addons-ecs.forgesvc.net/api/v2'
files_url = 'https://media.forgecdn.net/files'

downloading = False

class mod_downloader():

    def __init__(self, pb):
        self.pb = pb
        self.maxsteps = 1
        self.steps = 0

    def download(self, session, url, dest):
        print("Downloading %s" % url)
        r = session.get(url)
        with open(dest, 'wb') as f:
            f.write(r.content)
        self.steps += 1
        #self.pb.step((self.maxsteps / 500))
        print((self.maxsteps / 500) * self.steps)
        return r.status_code

    def get_json(self, session, url):
        r = session.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'})
        if r.status_code != 200:
            if r.status_code == 504:
                return self.get_json(session, url)
            print("Error %d trying to access %s" % (r.status_code, url))
            print(r.text)
            return None
        return json.loads(r.text)

    def fetch_mod(self, session, f, out_dir):
        pid = f['projectID']
        fid = f['fileID']
        project_info = self.get_json(session, api_url + ('/addon/%d' % pid))
        # print(project_info['websiteUrl'])
        file_type = project_info['websiteUrl'].split('/')[4] # mc-mods or texture-packs
        info = self.get_json(session, api_url + ('/addon/%d/file/%d' % (pid, fid)))
        if info is None:
            return None
        fn = info['fileName']
        dl = info['downloadUrl']
        out_file = out_dir + '/' + fn
        if os.path.exists(out_file):
            if os.path.getsize(out_file) == info['fileLength']:
                print("%s OK" % fn)
                return (out_file, file_type)
        self.download(session, dl, out_file)
        return (out_file, file_type)

    async def download_mods_async(self, manifest, out_dir):
        with ThreadPoolExecutor(max_workers=4) as executor, \
                requests.Session() as session:
            loop = asyncio.get_event_loop()
            tasks = []
            self.maxsteps = len(manifest['files'])
            for f in manifest['files']:
                task = loop.run_in_executor(executor, self.fetch_mod, *(session, f, out_dir))
                tasks.append(task)

            jars = []
            for resp in await asyncio.gather(*tasks):
                jars.append(resp)
            return jars


    def dwn(self, manifest_json, mods_dir):
        mod_jars = []
        with open(manifest_json, 'r') as f:
            manifest = json.load(f)
        print("Downloading mods")

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.download_mods_async(manifest, mods_dir))
        loop.run_until_complete(future)
        return future.result()

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
    global pb
    downloader = mod_downloader(pb)
    try:
        downloader.dwn(mf, dest)
    except:
        traceback.print_exc()
        if messagebox.askretrycancel(title="Error", message="An error occured while downloading files."):
            DownloadMods(mf, dest)


def install():
    if modpackZip == "" or modpackRoot == "":
        messagebox.showerror(title="Error", message="Please select a Modpack root and a Modpack Export")
    else:
        doit = askyesno(title="Install?", message="Are you sure you want to install " + modpackZip.split("/")[-1] + " into " + modpackRoot + " ?")
        if doit:
            os.makedirs(modpackRoot, exist_ok=True)
            os.makedirs(modpackRoot + "/temp", exist_ok=True)
            os.makedirs(modpackRoot + "/mods", exist_ok=True)
            with zipfile.ZipFile(modpackZip, 'r') as zip_ref:
                zip_ref.extractall(modpackRoot + "/temp")
            manifest = modpackRoot + "/temp" + "/manifest.json"
            DownloadMods(manifest, modpackRoot + "/mods")
            shutil.copytree(modpackRoot + "/temp/overrides", modpackRoot, dirs_exist_ok=True)
            shutil.rmtree(modpackRoot + "/temp")
            print("Done!")
            messagebox.showinfo(title="Done!", message="Done installing Modpack")

ttk.Label(frm, text="JoBlocks Modpack installer").grid(column=0, row=0)

ttk.Button(frm, text="Select Modpack Export", command=askModpackZip).grid(column=0, row=1)

ttk.Button(frm, text="Select Modpack Root", command=askModpackRoot).grid(column=0, row=2)

pb = ttk.Progressbar(root, orient=HORIZONTAL, length=500, mode="determinate").grid(column=0, row=4)

ttk.Button(frm, text="Install", command=install).grid(column=0, row=3)



ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=5)

root.mainloop()
