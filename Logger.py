# coding=utf8

import time

def interpret(line):
    Log = {}
    Log['line'] = line
    Log['time'] = lambda: int(round(time.time() * 1000))
    Log['nick'] = ''
    Log['ident'] = ''
    Log['host'] = ''
    Log['command'] = ''
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

    print('%s %s' % (time.strftime('%H:%M:%S', time.gmtime(Log['time'])), Log['line']))

    if Log['command'] == 'PRIVMSG':
        Log['context'] = Log['parameters'][0]
    else:
        Log['context'] = None
    
    return Log

def listActive(self, chan, fullLog, minutes = 10, caller = None, full = False, exclude = []):
    activeList = []
    validList = []
    timenow = lambda: int(round(time.time() * 1000))
    fLog = {k: v for k, v in fullLog.items() if ((timenow - k)/6000 <= minutes or full) and v['context'] == chan}
    fList = [fLog[k] for k in fLog.keys()]
    fList.reverse()
    
    uDict = list(self.userDict)
    gUDict = self.userDict[group]
    
    for group in uDict:
        if caller and caller in self.userDict[group]:
            userDict.remove(group)
            break
    for line in fList:
        for group in uDict:
            for unick in gUDict:
                if line['nick'].lower() == unick.lower():
                    validList.append(line['nick'])
                    del gUDict[unick]
                    break

    for key in validList:
        if key not in self.info['IGNORE'] and key != self.info['NICK'] and key not in exclude:
                activeList.append(key)
    return activeList
