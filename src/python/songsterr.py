import requests
import time

SONGSTERR = "https://www.songsterr.com/api/songs"
MB = "https://musicbrainz.org/ws/2/recording"
UA = {"User-Agent": "RiffFinder/0.1 ( andreicalota0305@gmail.com )"}


NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE = {n: NAMES[n % 12] for n in range(128)}


def format_tuning(t):
    return "".join(c for c in reversed(t) if not c.isspace())
    

# note i should make it return the link to the songsterr page in the json
def get_songsterr_data(song_name):
    r = requests.get('https://www.songsterr.com/api/songs', params={'pattern': song_name}).json()

    first = r[0]

 
    artist = first["artist"]
    title = first["title"]
  
    tracks = first['tracks']
    
    guitars = [t for t in tracks if 'guitar' in t['hash']]
    best = max(guitars, key=lambda t: t['views'])

    tuning = format_tuning([NOTE[m] for m in best["tuning"]])
   
    diff = best["difficulty"]
    views = best["views"]
 
    track = {'title': title, 'artist': artist, 'tuning': tuning, 'difficulty': diff, 'views': views, 'tags': []}
 
    return track
 


 
   