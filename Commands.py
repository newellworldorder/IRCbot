# coding=utf8

from bs4 import BeautifulSoup
import praw, re, requests, time

commands = {}

def redditAPI(self):
    try:
        self.r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit links')
        enableNSFW = self.r.get_random_subreddit(nsfw=True)
        self.redditEnabled = True
    except:
        self.redditEnabled = False

def nwodo(self,Log):
    if Log['host'] in self.info['SUDOER'] + self.info['OWNER']:
        self.ircSend(' '.join(Log['trail'][1:]))
commands['!nwodo'] = nwodo

def active(self,Log):
    if len(self.listActive(Log['context'])) == 1:
        self.PRIVMSG(Log['context'],'There is 1 active user here (only users identified with NickServ are included)')
    else:
        self.PRIVMSG(Log['context'],'There are %s active users in here (only users identified with NickServ are included)' % len(self.listActive(Log['context'])))
commands['!active'] = active

def activelist(self,Log):
    self.ircSend('NOTICE '+Log['nick']+' :%s' % ' '.join(self.listActive(Log['context'])))
commands['!activelist'] = activelist

def reddit(self,Log):
    if not self.redditEnabled:
        redditAPI(self)
    else:
        try:
            r = self.r
            redditItem = Log['trail'][1]
            if (len(Log['trail']) > 2 and Log['trail'][2].lower() != 'user') or len(Log['trail']) < 3:
                sub = None
                nsfwstatus = ''
                if len(Log['trail']) > 2:
                    category = Log['trail'][2].lower()
                    if category == 'controversial':
                        s = r.get_subreddit(redditItem.lower()).get_controversial(limit=1)
                    elif category == 'hot':
                        s = r.get_subreddit(redditItem.lower()).get_hot(limit=1)
                    elif category == 'new':
                        s = r.get_subreddit(redditItem.lower()).get_new(limit=1)
                    elif category == 'random':
                        sub = r.get_subreddit(redditItem.lower()).get_random_submission()
                    elif category == 'rising':
                        s = r.get_subreddit(redditItem.lower()).get_rising(limit=1)
                    elif category == 'search' and len(Log['trail']) > 3:
                        s = r.get_subreddit(redditItem.lower()).search('+'.join(Log['trail'][3:]),limit=1)
                    elif category == 'top':
                        s = r.get_subreddit(redditItem.lower()).get_top(limit=1)
                else:
                    sub = r.get_subreddit(redditItem.lower()).get_random_submission()
                if not sub:
                    sub = next(s)
                if sub.over_18:
                    nsfwstatus = 'NSFW '
                self.PRIVMSG(Log['context'],'07Reddit 04%s10%s - 12%s 14( %s )' % (nsfwstatus, sub.subreddit.url, sub.title, sub.url))
            elif (len(Log['trail']) > 2 and Log['trail'][2].lower() == 'user'):
                try:
                    user = r.get_redditor(redditItem)
                    self.PRIVMSG(Log['context'],'07Reddit 10%s 14( %s )' % (user.name, user._url))
                except:
                    self.PRIVMSG(Log['context'],'Reddit user \'%s\' does not exist.' % (redditItem))
        except:
            pass
commands['!reddit'] = reddit

def ud(self,Log):
    try:
        r = requests.get('http://api.urbandictionary.com/v0/define?term=%s' % '+'.join(Log['trail'][1:]))
        data = r.json()
        if data['result_type'] != 'no_results':
            definition = ' '.join(data['list'][0]['definition'].splitlines())
            truncated = ''
            if len(definition) >= 150:
                truncated = '...'
                definition = definition[:146]
            self.PRIVMSG(Log['context'],'Urban08Dictionary 12%s - 06%s%s 10( %s )' % (data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
        else:
            self.PRIVMSG(Log['context'],'No definition for %s' % ' '.join(Log['trail'][1:]))
    except:
        print('Error fetching definition')
        self.PRIVMSG(Log['context'],'I cannot fetch this definition at the moment')
commands['!ud'] = ud

def google(self,Log):
    url = 'https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:])
    r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(Log['trail'][1:]))
    if '/search?q=%s&btnI' % '+'.join(Log['trail'][1:]) in r.url:
        self.PRIVMSG(Log['context'],'12G04o08o12g03l04e 06[%s] 13%s' % (' '.join(Log['trail'][1:]), url[:-5]))
    else:
        r2 = requests.get(r.url, timeout=2)
        soup = BeautifulSoup(r.text)
        title = soup.title.text.strip()
        if title:
            linkinfo = ' – 03%s' % title
        self.PRIVMSG(Log['context'],'12G04o08o12g03l04e 12%s04%s 08( %s )' % (' '.join(Log['trail'][1:]), linkinfo, r.url))
commands['!google'] = google

def wiki(self,Log):
    search = '_'.join(Log['trail'][1:])
    url = 'http://en.wikipedia.org/wiki/%s' % search
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    title = soup.title.text.strip()
    content = soup.select('div > p')[0].text
    content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
    if content == 'Other reasons this message may be displayed:':
        self.PRIVMSG(Log['context'],'Wikipedia 03%s – 12No article found. Maybe you could write it: 11https://en.wikipedia.org/w/index.php?title=Special:UserLogin&returnto=%s' % (title, search))
    else:
        if 'may refer to:' in content:
            r = requests.get('http://en.wikipedia.org%s' % soup.find('ul').find('li').find('a')['href'])
            soup = BeautifulSoup(r.text)
            title = soup.title.text
            content = soup.select('div > p')[0].text
            content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
        exerpt = '. '.join(content.split('. ')[:1])
        if not exerpt[-1] in '!?.':
            exerpt = exerpt + '.'
        self.PRIVMSG(Log['context'],'Wikipedia 03%s – 12%s 11( %s )' % (title, exerpt, r.url))
commands['!wiki'] = wiki

def help_(self,Log):
    self.PRIVMSG(Log['context'],'My commands are: %s' % (' '.join(commands)))
commands['!help'] = help_

def about(self,Log):
    try:
        with open('about.txt', 'r') as file:
            self.PRIVMSG(Log['context'],file.readline())
    except:
        with open('about.txt', 'w+') as file:
            file.write('Hi, I\'m an IRC bot written by NewellWorldOrder/nwo')
commands['!about'] = about

def list_(self, Log):
    if Log['host'] in self.info['OWNER'] + self.info['SUDOER']:
        try:
            if Log['trail'][2].lower() == 'add':
                for item in Log['trail'][3:]:
                    if item not in self.info[Log['trail'][1].upper()]:
                        self.info[Log['trail'][1].upper()].append(item)
                        if Log['trail'][1].upper() == 'CHAN':
                            self.ircSend('JOIN %s' % item)
            elif Log['trail'][2].lower() == 'remove':
                for item in Log['trail'][3:]:
                    if item in self.info[Log['trail'][1].upper()]:
                        self.info[Log['trail'][1].upper()].remove(item)
                        if Log['trail'][1].upper() == 'CHAN':
                            self.ircSend('PART %s' % item)
            self.updateFile()
        except KeyError:
            self.ircSend('NOTICE %s :Requested field does not exist' % Log['nick'])
    else:
        self.ircSend('NOTICE %s :You are not authorized to perform that command' % Log['nick'])
commands['!list'] = list_

def Handler(self,Log):
    if Log['trail'][0].lower() in commands.keys():
        try:
            commands[Log['trail'][0].lower()](self,Log)
        except IndexError:
            self.ircSend('NOTICE %s :Invalid input for $s' % (Log['nick'],Log['trail'][0].lower()))
