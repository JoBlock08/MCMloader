from genericpath import exists
import sys
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter.messagebox import askyesno
import zipfile
import os
import mod_download
import platform
import shutil

root = Tk()

frm = ttk.Frame(root, padding=10)
frm.grid()

modpackZip = ""
modpackRoot = ""

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
        mod_download.dwn(mf, dest)
    except:
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

ttk.Button(frm, text="Install", command=install).grid(column=0, row=3)

ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=4)

root.mainloop()
