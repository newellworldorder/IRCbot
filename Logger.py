# -*- coding: utf-8 -*-

import time

def interpret(line):
    t = time.time()
    Log = {}
    Log['line'] = line
    Log['time'] = t
    Log['vTime'] = time.strftime("%H:%M:%S",time.gmtime(t))
    Log['nick'] = None
    Log['ident'] = None
    Log['host'] = None
    Log['command'] = None
    Log['parameters'] = []
    Log['trail'] = []
    words = str(line).split()
    if line[0] == ':':
        prefix = words.pop(0)[1:]
        if '!' in prefix and '@' in prefix:
            Log['nick'] = prefix.split('!')[0]
            Log['ident'] = prefix.split('!')[1].split('@')[0]
            Log['host'] = prefix.split('@')[1]
    if len(words) > 0:
        Log['command'] = words.pop(0)
        for i in range(len(words)):
            if words[0][0] == ':':
                break
            Log['parameters'].append(words.pop(0))

    if words:
        words[0] = words[0].lstrip(':+-')
        Log['trail'] = ' '.join(words).split()
    if Log['parameters']:
        Log['context'] = Log['parameters'][0]

    print('%s %s' % (Log['vTime'], Log['line']))

    return Log

def listActive(self, channel, timer = 10):
    t = time.time()
    activeList = []
    for nick in self.lastSeen[channel]:
        if type(nick) is str or not(nick['lastMessage']) or nick.lower() == caller.lower():
            continue
        if nick['lastAction'][1] == 'talk' or nick['lastAction'][1] == 'join':
            if nick['lastMessage'][0] < t - (timer * 60):
                activeList.append(nick)
    return activeList
