#!/usr/bin/python3
import os, logging, subprocess, queue, re, requests, threading, \
    shutil, time, sys, unidecode, argparse
from zipfile import ZipFile

DEFAULT_PLAYLIST="Z:\\Documents\\playlist.m3u"
DEFAULT_OUTPUT="Z:\\Music\\flac_phobic"
DEFAULT_RSYNC_STRIP="Z:\\Music\\"

FLAC_PHOBIC_DIR = os.path.dirname(os.path.realpath(__file__))
FFMPEG_PATH = os.path.join(FLAC_PHOBIC_DIR, 'ffmpeg.exe') # flac_phobic.py directory

parser = argparse.ArgumentParser(description='Create iTunes-compatible playlists from existing playlists, '
                                             'converting FLAC to mp3 as needed.')
parser.add_argument('-i', '--input', default=DEFAULT_PLAYLIST, metavar='[input playlist]', help='.m3u file with one track per line')
parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, metavar='[output directory]')
parser.add_argument('-q', '--quality', default='0', help='LAME VBR value (0, 1, 2, 3, etc.)')
parser.add_argument('--log', action='store_true', help='output log file in current directory.')
parser.add_argument('--rsync-strip', default=DEFAULT_RSYNC_STRIP, help='String to strip from beginning of rsync file-list.')

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
            if not os.path.exists(output):
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
                if LOGGING_ENABLED == True:
                    logging.info("output: %s", process.stderr)
                self.compressed.append(output)
            else:
                self.compressed.append(output)

    def compress_flacs(self):
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
        with open(playlist_path, 'w', encoding='utf8') as f:
            for each in self.static:
                f.write(each + "\n")
            for each in self.compressed:
                f.write(each + "\n")           
        print("")
        print("completed playlist output to " + playlist_path)

    def build_rsync_manifest(self):
        manifest_path = os.path.normpath(os.path.join(OUTPUT_DIRECTORY, 'rsync_manifest.txt'))
        with open(manifest_path, 'w', encoding='utf8') as f:
            for each in self.static:
                new_path = each.replace(RSYNC_STRIP, "").replace("\\", "/")
                f.write(new_path + "\n")
            for each in self.compressed:
                new_path = each.replace(RSYNC_STRIP, "").replace("\\", "/")
                f.write(new_path + "\n")

def main():
    global PLAYLIST, ENCODE_QUALITY, OUTPUT_DIRECTORY, LOGGING_ENABLED, RSYNC_STRIP
    args = parser.parse_args()
    PLAYLIST = os.path.abspath(args.input)
    OUTPUT_DIRECTORY = os.path.abspath(args.output)
    ENCODE_QUALITY = args.quality  # LAME VBR quality -- default V0    
    RSYNC_STRIP = args.rsync_strip
    if args.log == True:
        LOGGING_ENABLED = True
        logging.basicConfig(filename="flac_phobic.log", level=logging.INFO,
                    format='%(asctime)-15s %(message)s')
    else:
        LOGGING_ENABLED = False
    try:
        flac_phobic = FlacPhobic()
        flac_phobic.prep_workarea()
        flac_phobic.compress_flacs()
        flac_phobic.build_playlist()
        flac_phobic.build_rsync_manifest()
    except KeyboardInterrupt:
        flac_phobic.thread_kill_event.set()
        print("")
        print('allowing running encodes to finish...')
