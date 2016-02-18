# coding=utf8

import time

def interpret(info, raw):
    t = time.time()
    line = {'time':t,'nick':None,'ident':None,'host':None,'command':None,'parameters':[],'trail':[]}
    words = str(raw).split()
    if raw[0] == ':':
        prefix = words.pop(0)[1:]
        if '!' in prefix and '@' in prefix:
            line['nick'] = prefix.split('!')[0]
            line['ident'] = prefix.split('!')[1].split('@')[0]
            line['host'] = prefix.split('@')[1]
    if len(words) > 0:
        line['command'] = words.pop(0)
        for i in range(len(words)):
            if words[0][0] == ':':
                break
            line['parameters'].append(words.pop(0))

    if words:
        words[0] = words[0][1:]
        line['trail'] = ' '.join(words).split()

    if line['parameters']:
        line['context'] = line['parameters'][0]
        if line['context'] == info['NICK']:
            line['context'] = line['nick']

    print('%s %s' % (time.strftime("%H:%M:%S",time.gmtime(t)), raw))

    return line

def listActive(self, channel, timer = 10):
    t = time.time()
    activeList = []
    for nick in self.lastSeen[channel]:
        if type(nick) is str or not(nick['lastMessage']):
            continue
        if nick['lastAction'][1] == 'talk' or nick['lastAction'][1] == 'join':
            if nick['lastMessage'][0] < t - (timer * 60):
                activeList.append(nick)
    return activeList
