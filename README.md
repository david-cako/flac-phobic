# flac-phobic

Create iTunes-compatible playlists from existing playlists, converting flac to mp3 as needed

I listen to a lot of music, and it's pretty frustrating trying to maintain both a foobar2000 playlist on my Windows machine and an iTunes playlist for my iPhone sync.

Seeing as iTunes is incompatible with FLAC, and not wanting to convert a decent portion of my music library from a widely supported format to a less widely supported format, I've just dealt with it, manually converting and maintaining them separately.

flac-phobic eases the pain of this, taking an m3u as input, encoding all FLAC files as mp3, and constructing a new playlist containing all of the newly encoded mp3s, as well as all of the existing lossy files.  Encoded files are output into a new directory, with all of the original directory structure being maintained beneath it.

## Usage
`flac_phobic [-q QUALITY] playlist.m3u Z:/Music/flac_phobic/`

`{quality}` [accepts an integer from 0-9](https://trac.ffmpeg.org/wiki/Encode/MP3), and defaults to `0` (`V0`).

Make sure your playlists are just lists of files:

    Z:\Music\...\...\(...).mp3
    Z:\Music\...\(...).flac
    Z:\Music\...\...\...\(...).mp3

This script takes *every* line from the playlist, so any extraneous crap is going to be a problem.

foobar2000 refuses to output non-latin characters (I've really only had issues with Japanese and Chinese) correctly in its exported playlists, but flac-phobic *does* work with non-latin paths.  I've worked around this by just having a secondary iTunes playlist of files with non-latin paths that I manage manually.
