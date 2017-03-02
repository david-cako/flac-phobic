#!/usr/bin/python3

import os, logging, subprocess, queue, re, threading, signal, time, sys

PLAYLIST = 'playlist.m3u'
EXCLUDED_EXTENSIONS = b'(mp3 | wav | m4a | wma | ogg)'
ENCODE_QUALITY = "0"  # LAME VBR quality -- default V0
OUTPUT_DIRECTORY = os.path.expanduser('~/Music/flac_phobic')

logging.basicConfig(filename='flac_phobic.log', level=logging.INFO)

class FlacPhobic:
    def __init__(self, playlist): 
        self.flacs = []
        self.static = [] 
        self.compressed = []
        self.queue = queue.Queue()
        self.threads = []

        with open(playlist, 'r') as f:
            for line in f.readlines():
                if line.endswith('.flac\n'):
                    self.flacs.append(line.rstrip())
                if line.endswith('.mp3\n'):
                    self.static.append(line.rstrip())

    def compress_worker(self):
        while True:
            try:
                path, output = self.queue.get_nowait()
            except:
                break
            
            print("encoding file {} of {} - {}".format(self.total_queue_size - self.queue.qsize(), 
                                                self.total_queue_size, path), end='\r', flush=True)
            if self.old_playlist == None or output not in self.old_playlist:
                if not os.path.isdir(os.path.split(output)[0]):
                    os.makedirs(os.path.split(output)[0])
                process = subprocess.run(['ffmpeg', '-n', '-i', path, '-q:a', ENCODE_QUALITY, output],
                                        stderr=subprocess.PIPE)
                if process.returncode != 0:
                    logging.error("output: %s", process.stderr)
                else:
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
            output = os.path.normpath(OUTPUT_DIRECTORY + os.path.splitdrive(head)[1] + '/' + filename + '.mp3')
            self.queue.put((path, output))
            self.total_queue_size = self.queue.qsize()

        for i in range(4):
            thread = threading.Thread(target=self.compress_worker)
            thread.start()
            self.threads.append(thread)

        while threading.active_count() > 0:
            time.sleep(0.1)

        for thread in self.threads:
            thread.join()
            
    def build_playlist(self):
        playlist_path = os.path.normpath(os.path.join(OUTPUT_DIRECTORY, 'flac_phobic.m3u'))
        if not os.path.isdir(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        with open(playlist_path, 'w') as f:
            for each in self.static:
                f.write(each + "\n")
            for each in self.compressed:
                f.write(each + "\n")
        print("completed playlist output to " + playlist_path)

def handler(signum, frame):
    print('')
    flac_phobic.queue = ""
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

#def main():
flac_phobic = FlacPhobic(PLAYLIST)
flac_phobic.compress_flacs()
flac_phobic.build_playlist()
