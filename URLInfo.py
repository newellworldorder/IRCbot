# coding=utf8

from bs4 import BeautifulSoup
import requests

sites = {}

def youtubeKey():
    try:
        with open('youtubeAPI', 'r') as file:
            for line in file:
                if line.strip()[0] != '#':
                    APIkey = line.strip()
                    return APIkey
    except:
        with open('youtubeAPI', 'w+') as file:
            file.write('# Insert your YouTube API key below')
        return None

def youtube(self,line,url):
    if 'youtube.com/' in url or 'youtu.be/' in url:
        vidID = url.split('youtu.be/')[-1].split('v=')[-1].split('youtube.com/v/')[-1].split('#')[0].split('&')[0].split('?')[0]
        try:
            payload = {'part': 'snippet,statistics', 'id': vidID, 'key': youtubeKey()}
            r = requests.get('https://www.googleapis.com/youtube/v3/videos', params = payload)
            data = r.json()
            title = data['items'][0]['snippet']['title']
            channel = data['items'][0]['snippet']['channelTitle']
            likes = int(data['items'][0]['statistics']['likeCount'])
            dislikes = int(data['items'][0]['statistics']['dislikeCount'])
            votes = likes + dislikes
            if likes and dislikes:
                bar = '12' + str(likes) + ' ' + '—' * round(likes*10/votes) + '15' + '—' * round(dislikes*10/votes) + ' ' + str(dislikes)
            else:
                bar = ''
            self.PRIVMSG(line['context'],'You00,04Tube %s 14uploaded by %s – %s' % (title, channel, bar))
        except Exception as e:
            print(e)
sites['youtu.be/'] = youtube
sites['youtube.com/'] = youtube

def massdrop(self,line,url):
    if not '?mode=guest_open' in url:
        url = url + '?mode=guest_open'
    basic(self,line,url)
sites['massdrop.com/'] = massdrop

def basic(self,line,url):
    try:
        r = requests.get(url, timeout=2)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.text.strip()
        if title:
            self.PRIVMSG(line['context'],'03%s 09( %s )' % (title, url))
    except Exception as e:
        print(e)

def Handler(self,line):
    if 'http' in ''.join(line['trail']):
        for w in line['trail']:
            if w[:4] == 'http' and '://' in w:
                found = False
                for site in sites.keys():
                    if site in w:
                        sites[site](self,line,w)
                        found = True
                        break
                if not found:
                    basic(self,line,w)
