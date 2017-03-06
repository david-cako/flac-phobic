#!/usr/bin/python3
import os, logging, subprocess, queue, re, requests, threading, \
    shutil, time, sys, unidecode, argparse
from zipfile import ZipFile

parser = argparse.ArgumentParser(description='Create iTunes-compatible playlists from existing playlists, '
                                             'converting FLAC to mp3 as needed.')
parser.add_argument('playlist', metavar='[input playlist]', help='.m3u file with one track per line')
parser.add_argument('outputdir', metavar='[output directory]')
parser.add_argument('-q', '--quality', default='0', help='LAME VBR value (0, 1, 2, 3, etc.)')

FLAC_PHOBIC_DIR = os.path.dirname(os.path.realpath(__file__))
FFMPEG_PATH = os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg.exe') # flac_phobic.py directory

logging.basicConfig(filename="flac_phobic.log", level=logging.INFO,
                    format='%(asctime)-15s %(message)s')

class FlacPhobic:
    def __init__(self): 
        self.flacs = []
        self.static = [] 
        self.compressed = []
        self.queue = queue.Queue()
        self.threads = []
        self.isdir_lock = threading.Lock()
        self.thread_kill_event = threading.Event()
 
    def prep_workarea(self):
        global FFMPEG_PATH
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

        with open(PLAYLIST, 'r') as f:
            for line in f.readlines():
                if line.strip() and os.path.isfile(line.rstrip()): # no empty lines, no non-existent files
                    if line.endswith('.flac\n'):
                        self.flacs.append(line.rstrip())
                    else:
                        self.static.append(line.rstrip())
        if not os.path.isdir(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
    
    def compress_worker(self):
        while not self.thread_kill_event.is_set():
            try:
                path, output = self.queue.get_nowait()
            except:
                break
            print("encoding file {} of {} - {} -> {}{}".format(self.total_queue_size - self.queue.qsize(), 
                                                self.total_queue_size, path, output, " "*20), end='\r', flush=True)
            if self.old_playlist == None or output not in self.old_playlist:
                self.isdir_lock.acquire()
                if not os.path.isdir(os.path.split(output)[0]):
                    os.makedirs(os.path.split(output)[0])
                    if os.path.isfile(os.path.join(os.path.split(path)[0], 'folder.jpg')):
                        shutil.copy2(os.path.join(os.path.split(path)[0], 'folder.jpg'), os.path.split(output)[0])
                    if os.path.isfile(os.path.join(os.path.split(path)[0], 'folder.png')):
                        shutil.copy2(os.path.join(os.path.split(path)[0], 'folder.png'), os.path.split(output)[0])
                self.isdir_lock.release()
                process = subprocess.run([FFMPEG_PATH, '-n', '-i', path, '-q:a', ENCODE_QUALITY,
                                        '-map_metadata', '0', '-id3v2_version', '3', output],
                                        stderr=subprocess.PIPE)
                logging.info("output: %s", process.stderr)
                self.compressed.append(output)
            else:
                self.compressed.append(output)

    def compress_flacs(self):
        try:
            with open(os.path.join(OUTPUT_DIRECTORY, 'flac_phobic.m3u'), 'r') as f:
                self.old_playlist = f.readlines() # previous flac_phobic playlist, not the foobar playlist
        except:
            self.old_playlist = None
        for path in self.flacs:
            head, filename = os.path.split(path)
            filename, _ = os.path.splitext(filename)
            output = OUTPUT_DIRECTORY + os.path.splitdrive(head)[1] + '\\' + filename + '.mp3'
            self.queue.put((path, output))
            self.total_queue_size = self.queue.qsize()
        for i in range(4):
            thread = threading.Thread(target=self.compress_worker)
            thread.start()
            self.threads.append(thread)
        while threading.active_count() > 1:
            time.sleep(1)
        for thread in self.threads:
            thread.join()
            
    def build_playlist(self):
        playlist_path = os.path.normpath(os.path.join(OUTPUT_DIRECTORY, 'flac_phobic.m3u'))
        with open(playlist_path, 'w') as f:
            for each in self.static:
                f.write(each + "\n")
            for each in self.compressed:
                f.write(each + "\n")           
        print("")
        print("completed playlist output to " + playlist_path)

def main():
    try:
        args = parser.parse_args()
        PLAYLIST = args.playlist
        ENCODE_QUALITY = args.quality  # LAME VBR quality -- default V0
        OUTPUT_DIRECTORY = os.path.normpath(args.outputdir)
        flac_phobic = FlacPhobic()
        flac_phobic.prep_workarea()
        flac_phobic.compress_flacs()
        flac_phobic.build_playlist()
    except KeyboardInterrupt:
        flac_phobic.thread_kill_event.set()
        print("")
        print('allowing running encodes to finish...')
