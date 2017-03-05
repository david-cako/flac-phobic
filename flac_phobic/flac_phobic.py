#!/usr/bin/python3
import os, logging, subprocess, queue, re, requests, threading, \
    shutil, signal, time, sys
from zipfile import ZipFile

PLAYLIST = 'playlist.m3u'
ENCODE_QUALITY = "0"  # LAME VBR quality -- default V0
OUTPUT_DIRECTORY = os.path.expanduser('~/Music/flac_phobic')
FLAC_PHOBIC_DIR = os.path.dirname(os.path.realpath(__file__))
FFMPEG_PATH = os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg.exe') # flac_phobic.py directory

logging.basicConfig(filename='flac_phobic.log', level=logging.INFO)

class FlacPhobic:
    def __init__(self, playlist): 
        self.flacs = []
        self.static = [] 
        self.compressed = []
        self.queue = queue.Queue()
        self.threads = []
        self.isdir_lock = threading.Lock()
 
    def prep_workarea(self):
        if not os.path.isfile(FFMPEG_PATH):
            if shutil.which('ffmpeg') != None:
                FFMPEG_PATH = shutil.which('ffmpeg')
            else:
                r = requests.get('https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.zip', stream=True)
                zip_path = os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg.zip')
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                with ZipFile(zip_path, 'r') as ffzip:
                    ffzip.extract('ffmpeg-latest-win64-static/bin/ffmpeg.exe', FLAC_PHOBIC_DIR)
                    os.rename(os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg-latest-win64-static/bin/ffmpeg.exe'), FFMPEG_PATH)
                os.remove(zip_path)
                shutil.rmtree(os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg-latest-win64-static'))

        with open(playlist, 'r') as f:
            for line in f.readlines():
                if line.strip(): # no empty lines
                    if line.endswith('.flac\n'):
                        self.flacs.append(line.rstrip())
                    else:
                        self.static.append(line.rstrip())
        if not os.path.isdir(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
    
    def compress_worker(self):
        while True:
            try:
                path, output = self.queue.get_nowait()
            except:
                break
            print("encoding file {} of {} - {} {}".format(self.total_queue_size - self.queue.qsize(), 
                                                self.total_queue_size, path, " "*20), end='\r', flush=True)
            if self.old_playlist == None or output not in self.old_playlist:
                self.isdir_lock.acquire()
                if not os.path.isdir(os.path.split(output)[0]):
                    os.makedirs(os.path.split(output)[0])
                self.isdir_lock.release()
                process = subprocess.run([FFMPEG_PATH, '-n', '-i', path, '-q:a', ENCODE_QUALITY, output],
                                        stderr=subprocess.PIPE)
                logging.info("output: %s", process.stderr)
                self.compressed.append(output)
            else:
                self.compressed.append(output)

    def compress_flacs(self):
        os.chdir(OUTPUT_DIRECTORY)
        try:
            with open('flac_phobic.m3u', 'r') as f:
                self.old_playlist = f.readlines() # previous flac_phobic playlist, not the foobar playlist
        except:
            self.old_playlist = None
        for path in self.flacs:
            head, filename = os.path.split(path)
            filename, _ = os.path.splitext(filename)
            output = os.path.normpath(os.path.splitdrive(head)[1] + '/' + filename + '.mp3')
            self.queue.put((path, output))
            self.total_queue_size = self.queue.qsize()
        for i in range(4):
            thread = threading.Thread(target=self.compress_worker)
            thread.start()
            self.threads.append(thread)
        for thread in self.threads:
            thread.join()
            
    def build_playlist(self):
        playlist_path = 'flac_phobic.m3u'
        with open(playlist_path, 'w') as f:
            for each in self.static:
                f.write(each + "\n")
            for each in self.compressed:
                f.write(each + "\n")           
        print("")
        print("completed playlist output to " + playlist_path)

def handler(signum, frame):
    flac_phobic.queue = ""
    print("")
    print('allowing running encodes to finish...')

signal.signal(signal.SIGINT, handler)

def main():
    flac_phobic = FlacPhobic(PLAYLIST)
    flac_phobic.prep_workarea()
    flac_phobic.compress_flacs()
    flac_phobic.build_playlist()
