# coding=utf8

import re

def Soaker(self):
    self.soakOptionQueue = []

def tip(self,Log):
    soakOptions = {}
    soakOptions['nick'] = Log['nick']
    soakOptions['all'] = False
    soakOptions['exclude'] = []
    if len(Log['trail']) > 3:
        if 'all' in Log['trail'][3:]:
            soakOptions['all'] = True
        exclude = re.compile('[-]{1}\w+')
        for nicks in exclude.findall(' '.join(Log['trail'][3:])):
            soakOptions['exclude'].append(nicks[1:])
    self.soakOptionQueue.append(soakOptions)

def confirm(self,Log):
    tipper = Log['trail'][1]
    soakopt = self.soakOptionQueue.pop(0)
    initAmount = int(Log['trail'][4][1:])
    activeUser = self.listActive(Log['context'],10,tipper,soakopt['all'],soakopt['exclude'])
    if len(activeUser) > 0:
        tipAmount = initAmount // len(activeUser)
        if tipAmount >= 10:
            self.PRIVMSG('Doger','mtip %s %s' % ((' %s ' % tipAmount).join(activeUser),tipAmount))
            self.PRIVMSG(Log['context'],'%s is tipping %s shibes with Ɖ%s: %s' % (tipper, len(activeUser), tipAmount, ', '.join(activeUser)))
        else:
            self.PRIVMSG('Doger','mtip %s %s' % (tipper, initAmount))
            self.PRIVMSG(Log['context'],'Sorry %s, not enough to go around. Returning tip.' % tipper)
    else:
        self.PRIVMSG('Doger','mtip %s %s' % (tipper, initAmount))
        self.PRIVMSG(Log['context'],'Sorry %s, nobody is active! Returning tip.' % tipper)
            
def Handler(self,Log):
    if len(Log['trail']) < 2: return
    if Log['trail'][0].lower() == '!tip' and Log['trail'][1].lower() == self.info['NICK'].lower():
        tip(self,Log)
    elif Log['nick'] == 'Doger' and len(Log['trail']) > 6 and Log['trail'][0] == 'Such' and Log['trail'][6].rstrip('!').lower() == self.info['NICK'].lower():
        confirm(self,Log)
