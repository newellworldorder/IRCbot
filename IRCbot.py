# coding=utf8

from bs4 import BeautifulSoup
from operator import itemgetter
import base64, Commands, Config, praw, re, requests, Soaker, socket, ssl, time, URLInfo

class IRC:
    def __init__(self):
        Config.config(self)
        self.activeDict = {}
        for channel in self.info['CHAN'].split(','):
            self.activeDict[channel] = {}
        Commands.redditAPI(self)
        Soaker.Soaker(self)
        self.Connect()
        self.Main()
        
    def Connect(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(sock)
        connectMSG = []
        if self.SASL:
            connectMSG.append('CAP LS')
        connectMSG.append('NICK %s' % self.info['NICK'])
        connectMSG.append('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        connectMSG.append('JOIN %s' % self.info['CHAN'])
        self.irc.send(bytes('\r\n'.join(connectMSG)+'\r\n', 'UTF-8'))
        
    def Main(self):
        while True:
            serverRaw = self.irc.recv(4096).decode('utf-8')
            serverOut = str(serverRaw).split('\n')
            for line in serverOut:
                if len(line) < 1:
                    continue
                print (line)
                Log = {}
                Log['line']=line
                timenow = time.mktime(time.gmtime())
                words = str(line).split()
                prefix = ''
                nick = ''
                ident = ''
                host = ''
                trail = []
                parameters = []
                if line[0] == ':':
                    prefix = words.pop(0)[1:]
                    if '!' in prefix and '@' in prefix:
                        nick = prefix.split('!')[0]
                        ident = prefix.split('!')[1].split('@')[0]
                        host = prefix.split('@')[1]
                if len(words) > 0:
                    command = words.pop(0)
                    for i in range(len(words)):
                        if words[0][0] == ':':
                            break
                        parameters.append(words.pop(0))
                trail = ' '.join(words).split()
                if len(trail) > 0 and len(trail[0]) > 0:
                    trail[0] = trail[0][1:]
                    if len(trail[0]) > 0 and (trail[0][0] == '+' or trail[0][0] == '-'):
                        CAP = trail[0][0]
                        trail[0] = trail[0][1:]

                # reply to pings
                if command == 'PING':
                    self.ircSend('PONG :%s' % trail[0])
                    continue

                # SASL
                if self.SASL:
                    if command == 'CAP':
                        if parameters [0] == '*' and parameters[1] == 'LS':
                            self.ircSend('CAP REQ :%s' % ' '.join(trail))
                            continue
                        if parameters [1] == 'ACK':
                            self.ircSend('AUTHENTICATE PLAIN')
                            continue
                    if command == 'AUTHENTICATE' and parameters[0] == '+':
                        sasl_token = '\0'.join((self.info['NICK'], self.info['NICK'], self.info['PASS']))
                        self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        continue
                    if command == '903':
                        self.ircSend('CAP END')
                        self.ircSend('JOIN %s' % self.info['CHAN'])
                        continue

                # checks when identified with nickserv
                if command == 'NOTICE' and nick == 'NickServ':
                    if len(trail) > 3:
                        if 'registered' in trail[3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            continue
                        if trail[3] == 'identified':
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            continue

                # checks for INVITE received
                if command == 'INVITE' and parameters[0] == self.info['NICK']:
                    if trail[0] not in self.info['CHAN'].split(','):
                        self.info['CHAN'] = str(self.info['CHAN'])+','+trail[0]
                        self.updateFile()
                        self.ircSend('JOIN %s' % self.info['CHAN'])
                        
                # checks channel join
                if command == 'JOIN':
                    if nick == self.info['NICK']:
                        self.activeDict[parameters[0]] = {}
                        self.ircSend('WHO %s %%na' % parameters[0])
                    elif nick not in self.activeDict[parameters[0]]:
                        self.activeDict[parameters[0]][nick] = 0
                        if nick not in self.userDict.values():
                            self.ircSend('WHOIS %s' % trail[0])
                    continue

                # checks nick change
                if command == 'NICK':
                    if nick == self.info['NICK']:
                        self.info['NICK'] = trail[0]
                    else:
                        self.ircSend('WHOIS %s' % trail[0])
                    continue

                # parses NAMES result
                if str(command) == '353' and len(parameters) > 2:
                    if parameters[-1] not in self.activeDict:
                        self.activeDict[parameters[-1]] = {}
                    for names in trail:
                        if names != self.info['NICK']:
                            self.activeDict[parameters[-1]][names] = 0
                    continue
                    
                # parses WHOIS result
                if (str(command) == '330' or str(command) == '354') and len(parameters) > 2:
                    if parameters[2] not in self.userDict:
                        self.userDict[parameters[2]] = []
                    if parameters[1] not in self.userDict[parameters[2]] and parameters[1] != self.info['NICK']:
                        self.userDict[parameters[2]].append(parameters[1])
                    self.updateFile()
                    continue

                # updates active list if user leaves
                if command == 'PART':
                    if nick in self.activeDict[parameters[0]]:
                        del self.activeDict[parameters[0]][nick]
                    continue
                if command == 'QUIT':
                    for channels in self.info['CHAN'].split(','):
                        if nick in self.activeDict[channels]:
                            del self.activeDict[channels][nick]
                    continue

                # checks when PRIVMSG received
                if command == 'PRIVMSG':
                    Log['nick']=nick
                    Log['ident']=ident
                    Log['host']=host
                    Log['trail']=trail
                    Log['context']=parameters[0]
                    
                    def commandValid(cmd,minwords=1):
                        if len(trail) >= minwords and cmd in trail[0].lower() and len(trail[0]) <= len(cmd) + 1:
                            return True
                        else:
                            return False

                    # builds last spoke list
                    if Log['context'] not in self.activeDict:
                        self.activeDict[Log['context']] = {}
                    self.activeDict[Log['context']][Log['nick']] = timenow
                    validList = []
                    for group in self.userDict.values():
                        validList.extend(group)
                    if nick not in validList and CAP == '+':
                        self.ircSend('WHOIS %s' % nick)

                    # list modifier commands
                    if len(trail) > 2 and (trail[1].lower() == 'add' or trail[1].lower() == 'remove'):
                        def addRemoveList(issuer,issuerNick,command,additem,addcat):
                            if issuer in self.info['SUDOER'].split(',') or issuer in self.info['OWNER'].split(','):
                                if command == 'add':
                                    for item in additem:
                                        if item not in self.info[addcat]:
                                            self.info[addcat] = self.info[addcat]+','+item
                                elif command == 'remove':
                                    for item in additem:
                                        if item in self.info[addcat].split(','):
                                            updatedList = self.info[addcat].split(',')
                                            updatedList.remove(item)
                                            self.info[addcat] = ','.join(updatedList)
                                self.updateFile()
                            else:
                                self.ircSend(issuerNick,'NOTICE %s :You are not authorized to perform that command' % issuerNick)

                        # adds channels to autojoin list and joins them
                        if commandValid('!channel',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'CHAN')
                            self.ircSend('JOIN %s' % self.info['CHAN'])
                            if trail[1].lower() == 'remove':
                                self.ircSend('PART %s' % ','.join(trail[2:]))
                            continue

                        # adds users to ignore list (ie: bots)
                        if commandValid('!ignore',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'IGNORE')
                            continue

                        # adds users to sudoer list (ie: admins)
                        if commandValid('!admin',3):
                            addRemoveList(host,nick,trail[1].lower(),trail[2:],'SUDOER')
                            continue
                                
                    Soaker.Handler(self, Log)

                    Commands.Handler(self, Log)
                    
                    URLInfo.Handler(self, Log)
        
    def updateFile(self):
        with open('nwobot.conf', 'w+') as file:
            file.write(str(self.info))
        with open('users', 'w+') as file:
            file.write(str(self.userDict))
    
    def listActive(self,chan,minutes=10,caller=None,full=False,exclude=[]):
        activeList = []
        validList = []
        timenow = time.mktime(time.gmtime())
        userDict = list(self.userDict)
        mostRecent = list(dict(sorted(self.activeDict[chan].items(), key=itemgetter(1), reverse=True)).keys())
        for group in userDict:
            nickList = self.userDict[group]
            if caller != None and caller in nickList:
                userDict.remove(group)
                break
        for rnick in mostRecent:
            for group in userDict:
                nickList = self.userDict[group]
                for unick in nickList:
                    if rnick == unick:
                        validList.append(rnick)
                        userDict.remove(group)
                        break
        for key in validList:
            if key not in self.info['IGNORE'].split(',') and key != self.info['NICK'] and key not in exclude and (timenow - self.activeDict[chan][key] <= minutes * 60 or full):
                    activeList.append(key)
        return activeList
                        
    def PRIVMSG(self,con,msg):
        self.ircSend('PRIVMSG %s :%s' % (con,msg))

    def ircSend(self,msg):
        print(msg)
        self.irc.send(bytes(str(msg)+'\r\n', 'UTF-8'))
        
IRC()