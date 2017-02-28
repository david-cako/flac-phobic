#!/usr/bin/python

import os, logging, subprocess

PLAYLIST = 'playlist.fpl'
EXCLUDED_EXTENSIONS = b'(mp3 | wav | m4a | wma | ogg)'
ENCODE_QUALITY = "0"  # LAME VBR quality -- default V0
OUTPUT_DIRECTORY = path.expanduser('~/Music/flac_phobic/')

logging.basicConfig(filename='flac_phobic.log', level=logging.INFO)

class FlacPhobic:
    def __init__(self, playlist): 
        self.flacs = []
        self.static = [] 
        self.compressed = []
        self.queue = queue.Queue()
        self.threads = []

        with open(playlist, 'rb') as f:
            for line in f.readlines():
                self.static.extend(re.findall(b'file://.*?.' + EXCLUDED_EXTENSIONS, line))
                self.flacs.extend(re.findall(b'file://.*?.flac', line))

    def compress_worker(self):
        while True:
            try:
                path, output = self.queue.get_nowait()
            except:
                break
            
            print("encoding file {} of {}", queue.qsize(), self.queue_size, end="\r", flush=True)
            if self.old_playlist == None or output not in self.old_playlist:
                encode = subprocess.run(['ffmpeg', '-i', path, '-q:a', ENCODE_QUALITY, output],
                                        stderr=subprocess.PIPE)
                if encode.returncode != 0:
                    logging.error("failed converting: %s\n output: %s", filename, encode.stderr)
                else:
                    self.compressed.append(output)
            else:
                self.compressed.append(output)


    def compress_flacs(self)
        try:
            with open(os.path.join(OUTPUT_DIRECTORY, 'flac_phobic.m3u'), 'r') as f:
                self.old_playlist = f.readlines() # previous flac_phobic playlist, not the foobar playlist
        except:
            self.old_playlist = None
        
        for path in flacs:
            _, path = path.splitdrive(path.normpath(path))
            head, filename = path.split(path)
            filename, _ = os.path.splitext(filename)
            output = path.join(OUTPUT_DIRECTORY, head, filename + '.mp3') 
            self.queue.put((path, output))
            self.queue_size = queue.qsize()

        for i in range(4):
            thread = threadingThread(target=compression_worker)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
            
    def build_playlist(self)
        playlist_path = os.path.join(OUTPUT_DIRECTORY, 'flac_phobic.m3u')
        with open(playlist_path, 'w') as f:
            for each in self.static:
                f.write(each + "\n")
            for each in self.flacs:
                f.write(each + "\n")
        print("completed playlist output to {}", playlist_path)

def main():
    flac_phobic = FlacPhobic(PLAYLIST)
    flac_phobic.compress_flacs()
    flac_phobic.build_playlist()
