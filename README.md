# flac-phobic

Create iTunes-compatible playlists from existing playlists, converting flac to mp3 as needed

I listen to a lot of music, and it's pretty frustrating trying to maintain both a foobar2000 playlist and an iTunes playlist on my Windows machine for my iPhone sync.

Seeing as iTunes is incompatible with FLAC, and not wanting to convert a decent portion of my music library from a widely supported format to a less widely supported format, I've just dealt with it, manually converting and maintaining them separately.

flac-phobic eases the pain of this, taking an m3u as input, encoding all FLAC files as mp3, and constructing a new playlist containing all of the newly encoded mp3s, as well as all of the existing lossy files.  Encoded files are output into a new directory, with all of the original directory structure being maintained beneath it.

##Usage
##arguments not yet implemented
`flac_phobic playlist.m3u {-q quality} {-o output directory}`

`{quality}` [accepts an integer from 0-9](https://trac.ffmpeg.org/wiki/Encode/MP3), and defaults to `0` (`V0`).

`{output directory}` defaults to `~/Music/flac_phobic/`.

Make sure your playlists are just lists of files:

    Z:\Music\...\...\(...).mp3
    Z:\Music\...\(...).flac
    Z:\Music\...\...\...\(...).mp3

This script takes *every* line from the playlist, so any extraneous crap is going to be a problem.
