#!/usr/bin/env python3
import os
from tkinter.ttk import Progressbar
import requests
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tkinter import *
from tkinter import ttk

api_url = 'https://addons-ecs.forgesvc.net/api/v2'
files_url = 'https://media.forgecdn.net/files'



class mod_downloader():

    def __init__(self):
        self.steps = 0
        self.maxsteps = 0

    def download(self, session, url, dest):
        print("Downloading %s" % url)
        r = session.get(url)
        with open(dest, 'wb') as f:
            f.write(r.content)
        self.steps += 1
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
