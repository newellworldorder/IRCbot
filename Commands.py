# coding=utf8

from bs4 import BeautifulSoup
from datetime import datetime
from random import randint
import praw, re, requests, sys, time

commands = {}

def redditAPI(self):
    try:
        self.r = praw.Reddit('redFetch by u/NewellWorldOrder''Fetches reddit links')
        enableNSFW = self.r.get_random_subreddit(nsfw=True)
        self.redditEnabled = True
    except:
        self.redditEnabled = False

def formatList(inList):
    output = inList
    if len(inList) > 1:
        output = inList
        output[-1] = 'and ' + str(output[-1])
        if len(inList) > 2:
            return ', '.join(output)
    return ' '.join(output)

def timeDiffToString(t1, t2):
    t1D = datetime.utcfromtimestamp(t1)
    t2D = datetime.utcfromtimestamp(t2)
    elapsedTime = t2D - t1D
    d = elapsedTime.days
    m, s = divmod(elapsedTime.seconds, 60)
    h, m = divmod(m, 60)
    outList = []
    if not(d) and not(h) and not(m) and not(s):
        return 'now'
    if d:
        outList.append('%d days' % d)
    if h:
        outList.append('%d hours' % h)
    if m:
        outList.append('%d minutes' % m)
    if s:
        outList.append('%d seconds' % s)
    return formatList(outList)+' ago'

def seenRecurse(t, query, lastSeen):
    if type(lastSeen[query]) == str:
        return seenRecurse(t, lastSeen[query], lastSeen)
    else:
        lastAction = lastSeen[query]['lastAction']
        lastMessage = lastSeen[query]['lastMessage']
        tDiff = timeDiffToString(lastAction[0], t)
        output = '%s was last seen %sing %s' % (query, lastAction[1], tDiff)
        if lastMessage or len(lastAction) > 2:
            if (lastAction[1] == 'quitt' or lastAction[1] == 'leav') and len(lastAction[2]) > 0:
                output += ', saying \"%s\"' % lastAction[2]
            else:
                output += ', saying \"%s\"' % lastMessage[1]
        return output + '.'

def seen(self,line):
    if line['trail'][1].lower() in [x.lower() for x in self.lastSeen[line['context']]]:
        for nick in self.lastSeen[line['context']]:
            if nick.lower() == line['trail'][1].lower():
                self.PRIVMSG(line['context'], seenRecurse(time.time(), nick, self.lastSeen[line['context']]))
                break
    else:
        self.PRIVMSG(line['context'], 'I have not seen \"%s\".' % line['trail'][1])
commands['seen'] = seen

def bmiCalc(self,line):
    trail = ''.join(line['trail'][1:])
    kg = 0
    m = 0
    heights = [#[['mm','millimet'], 0.001],
               [['cm','centimet'], 0.01],
               [['dm','decimet'], 0.1],
               [['m','met'], 1],
               [['\'','ft','feet','foot'], 0.3048],
               [['\"','in'], 0.0254],
               [['yr','yard'], 0.9144]]
    masses = [[['mg','milligram'], 0.000001],
              [['cg','centigram'], 0.00001],
              [['dg','decigram'], 0.0001],
              [['g','gram'], 0.001],
              [['kg','kilogram'], 1],
              [['oz','ou'], 0.0283495],
              [['lb','pound'], 0.453592],
              [['st','stone'], 6.35029]]
    for units in heights:
        for name in units[0]:
            if name in trail:
                regex = '(\d+[.])?\d+[%s]' % name
                p = re.compile(regex)
                if p.search(trail):
                    m += float(re.sub("\D", "", p.search(trail).group())) * units[1]
                    break
    for units in masses:
        for name in units[0]:
            if name in trail:
                regex = '(\d+[.])?\d+[%s]' % name
                p = re.compile(regex)
                if p.search(trail):
                    kg += float(re.sub("\D", "", p.search(trail).group())) * units[1]
                    break
    if m > 0 and kg > 0:
        bmi = kg/(m*m)
        bmiStr = format(bmi, '.2f')
        output = 'Your BMI is %s' % bmiStr
        if bmi >= 30.0:
            output += ', you are 04obese'
        elif bmi >= 25.0:
            output += ', you are 07overweight'
        elif bmi >= 18.5:
            output += ', you are 09normal'
        else:
            output += ', you are 08underweight'
        self.PRIVMSG(line['context'],output + '\017.')
    else:
        self.PRIVMSG(line['context'],'Give me valid inputs. I accept inputs in most real units.')
commands['bmi'] = bmiCalc

def diceRoller(self,line):
    if 'd' in line['trail'][1].lower():
        try:
            numRolls = int(line['trail'][1].lower().split('d')[0])
            dieEdges = int(line['trail'][1].lower().split('d')[1])
        except:
            self.PRIVMSG(line['context'], 'Invalid roll: %s' % line['trail'][1])
        sumRolls = 0
        if numRolls >= 0 and dieEdges > 0 and dieEdges * numRolls < sys.maxsize:
            i = 0
            while i < numRolls:
                sumRolls += randint(1, dieEdges)
                i += 1
            self.PRIVMSG(line['context'], '%d' % sumRolls)
        else:
            self.PRIVMSG(line['context'], 'Invalid roll: %s' % line['trail'][1])
    else:
        self.PRIVMSG(line['context'], 'Invalid roll: %s' % line['trail'][1])
commands['roll'] = diceRoller

def active(self,line):
    if len(self.listActive(line['context'])) == 1:
        self.PRIVMSG(line['context'],'There is 1 active user here.')
    else:
        self.PRIVMSG(line['context'],'There are %s active users in here.' % len(self.listActive(line['context'])))
commands['active'] = active

def activelist(self,line):
    self.ircSend('NOTICE %s %s' % (line['nick'], formatList(self.listActive(line['context']))))
commands['activelist'] = activelist

def reddit(self,line):
    if not self.redditEnabled:
        redditAPI(self)
    else:
        try:
            r = self.r
            redditItem = line['trail'][1]
            if (len(line['trail']) > 2 and line['trail'][2].lower() != 'user') or len(line['trail']) < 3:
                sub = None
                nsfwstatus = ''
                if len(line['trail']) > 2:
                    category = line['trail'][2].lower()
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
                    elif category == 'search' and len(line['trail']) > 3:
                        s = r.get_subreddit(redditItem.lower()).search('+'.join(line['trail'][3:]),limit=1)
                    elif category == 'top':
                        s = r.get_subreddit(redditItem.lower()).get_top(limit=1)
                else:
                    sub = r.get_subreddit(redditItem.lower()).get_random_submission()
                if not sub:
                    sub = next(s)
                if sub.over_18:
                    nsfwstatus = 'NSFW '
                self.PRIVMSG(line['context'],'07Reddit 04%s10%s - 12%s 14( %s )' % (nsfwstatus, sub.subreddit.url, sub.title, sub.url))
            elif (len(line['trail']) > 2 and line['trail'][2].lower() == 'user'):
                try:
                    user = r.get_redditor(redditItem)
                    self.PRIVMSG(line['context'],'07Reddit 10%s 14( %s )' % (user.name, user._url))
                except:
                    self.PRIVMSG(line['context'],'Reddit user \'%s\' does not exist.' % (redditItem))
        except Exception as e:
            print(e)
            pass
commands['reddit'] = reddit

def ud(self,line):
    try:
        r = requests.get('http://api.urbandictionary.com/v0/define?term=%s' % '+'.join(line['trail'][1:]))
        data = r.json()
        if data['result_type'] != 'no_results':
            definition = ' '.join(data['list'][0]['definition'].splitlines())
            truncated = ''
            if len(definition) >= 150:
                truncated = '...'
                definition = definition[:146]
            self.PRIVMSG(line['context'],'Urban08Dictionary 12%s - 06%s%s 10( %s )' % (data['list'][0]['word'], definition[:149], truncated, data['list'][0]['permalink']))
        else:
            self.PRIVMSG(line['context'],'No definition for %s' % ' '.join(line['trail'][1:]))
    except:
        print('Error fetching definition')
        self.PRIVMSG(line['context'],'I cannot fetch this definition at the moment')
commands['ud'] = ud

def google(self,line):
    url = 'https://www.google.com/search?q=%s&btnI' % '+'.join(line['trail'][1:])
    r = requests.get('https://www.google.com/search?q=%s&btnI' % '+'.join(line['trail'][1:]))
    if '/search?q=%s&btnI' % '+'.join(line['trail'][1:]) in r.url:
        self.PRIVMSG(line['context'],'12G04o08o12g03l04e 06[%s] 13%s' % (' '.join(line['trail'][1:]), url[:-5]))
    else:
        r2 = requests.get(r.url, timeout=2)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.text.strip()
        if title:
            linkinfo = ' – 03%s' % title
        self.PRIVMSG(line['context'],'12G04o08o12g03l04e 12%s04%s 08( %s )' % (' '.join(line['trail'][1:]), linkinfo, r.url))
commands['google'] = google

def wiki(self,line):
    search = '_'.join(line['trail'][1:])
    url = 'http://en.wikipedia.org/wiki/%s' % search
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.text.strip()
    content = soup.select('div > p')[0].text
    content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
    if content == 'Other reasons this message may be displayed:':
        self.PRIVMSG(line['context'],'Wikipedia 03%s – 12No article found. Maybe you could write it: 11https://en.wikipedia.org/w/index.php?title=Special:Userlinein&returnto=%s' % (title, search))
    else:
        if 'may refer to:' in content:
            r = requests.get('http://en.wikipedia.org%s' % soup.find('ul').find('li').find('a')['href'])
            soup = BeautifulSoup(r.text,  "html.parser")
            title = soup.title.text
            content = soup.select('div > p')[0].text
            content = re.sub('\'','\\\'',re.sub('\\n','',re.sub('\[.*?\]','',content)))
        exerpt = '. '.join(content.split('. ')[:1])
        if not exerpt[-1] in '!?.':
            exerpt = exerpt + '.'
        self.PRIVMSG(line['context'],'Wikipedia 03%s – 12%s 11( %s )' % (title, exerpt, r.url))
commands['wiki'] = wiki

def help_(self,line):
    self.PRIVMSG(line['context'],'My commands are: %s' % (' '.join(commands)))
commands['help'] = help_

def about(self,line):
    try:
        with open('about.txt', 'r') as file:
            self.PRIVMSG(line['context'],file.readline())
    except:
        with open('about.txt', 'w+') as file:
            file.write('Hi, I\'m an IRC bot')
commands['about'] = about

def list_(self, line):
    if line['host'] in self.info['OWNER'] + self.info['SUDOER']:
        try:
            changed = []
            if line['trail'][2].lower() == 'add':
                for item in line['trail'][3:]:
                    if item not in self.info[line['trail'][1].upper()]:
                        self.info[line['trail'][1].upper()].append(item)
                        changed.append(item)
                        if line['trail'][1].upper() == 'CHAN':
                            self.ircSend('JOIN %s' % item)
                if len(changed) > 0:
                    self.ircSend('NOTICE %s :%s added to list: %s' % (line['nick'], str(changed).strip('[]'), line['trail'][1].upper()))
                else:
                    self.ircSend('NOTICE %s :Nothing was added to list: %s' % (line['nick'], line['trail'][1].upper()))
            elif line['trail'][2].lower() == 'remove':
                for item in line['trail'][3:]:
                    if item in self.info[line['trail'][1].upper()]:
                        self.info[line['trail'][1].upper()].remove(item)
                        changed.append(item)
                        if line['trail'][1].upper() == 'CHAN':
                            self.ircSend('PART %s' % item)
                if len(changed) > 0:
                    self.ircSend('NOTICE %s :%s removed from list: %s' % (line['nick'], str(changed).strip('[]'), line['trail'][1].upper()))
                else:
                    self.ircSend('NOTICE %s :Nothing was removed from list: %s' % (line['nick'], line['trail'][1].upper()))
            self.updateFile()
        except KeyError:
            self.ircSend('NOTICE %s :Command invalid, please use !list <list> <add/remove> <items>' % line['nick'])
    else:
        self.ircSend('NOTICE %s :You are not authorized to perform that command' % line['nick'])
commands['list'] = list_

def Handler(self,line):
    try:
        if line['trail'][0][0] == '@' and line['trail'][0].lower()[1:] in commands:
            commands[line['trail'][0][1:].lower()](self,line)
        elif line['trail'][0][0] == '@':
            self.PRIVMSG(line['context'], 'Error: Let\'s dispel once and for all with this fiction that Barack Obama doesn\'t know what he\'s doing. He knows exactly what he\'s doing. (command not recognized)')
    except IndexError:
        self.ircSend('NOTICE %s :Invalid input for $s' % (line['nick'],line['trail'][0]))
