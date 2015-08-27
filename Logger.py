# coding=utf8

import time

def current_milli_time():
    return int(round(time.time() * 1000))

def interpret(line):
    t = time.time()
    Log = {}
    Log['line'] = line
    Log['time'] = current_milli_time()
    Log['nick'] = None
    Log['ident'] = None
    Log['host'] = None
    Log['command'] = None
    Log['parameters'] = []
    Log['cap'] = ''
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

    Log['trail'] = ' '.join(words).split()
    if len(Log['trail']) > 0 and len(Log['trail'][0]) > 0:
        Log['trail'][0] = Log['trail'][0][1:]
        if len(Log['trail'][0]) > 0 and (Log['trail'][0][0] == '+' or Log['trail'][0][0] == '-'):
            Log['cap'] = Log['trail'][0][0]
            Log['trail'][0] = Log['trail'][0][1:]

    fmt = u'%H:%M:%S'
    print('%s %s' % (time.strftime(fmt.encode('utf-8', time.gmtime(t)).decode('utf-8').strip(), Log['line']))

    if Log['command'] != None and Log['command'] == 'PRIVMSG':
        Log['context'] = Log['parameters'][0]
    else:
        Log['context'] = None
    
    return Log

def listActive(self, chan, minutes = 10, caller = None, full = False, exclude = []):
    activeList = []
    validList = []
    timenow = current_milli_time()
    fLog = {k: v for k, v in self.fLog.items() if ((timenow - k)/6000 <= minutes or full) and v['context'] == chan}
    fList = [self.fLog[k] for k in fLog.keys()]
    fList.reverse()
    uDict = list(self.userDict)
    userDict = self.userDict
    
    if caller:
        cAccount = []
        for nick in self.userDict[caller]:
            cAccount.append(nick.lower())
        fList = [i for i in fList if i['nick'].lower() not in cAccount]
        
    for line in fList:
        for group in uDict:
            gUDict = userDict[group]
            for unick in gUDict:
                if line['nick'].lower() == unick.lower():
                    validList.append(line['nick'])
                    uDict.remove(group)
                    fList = [i for i in fList if i['nick'] != line['nick']]
                    break

    for key in validList:
        if key not in self.info['IGNORE'] and key != self.info['NICK'] and key not in exclude:
                activeList.append(key)
    return activeList
