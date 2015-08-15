# coding=utf8

from bs4 import BeautifulSoup
from operator import itemgetter
import base64, Commands, Config, importlib, Logger, praw, re, requests, Soaker, socket, ssl, time, types, URLInfo

class IRC:
    def __init__(self):
        Config.config(self)
        self.activeDict = {}
        for channel in self.info['CHAN']:
            self.activeDict[channel] = {}
        Commands.redditAPI(self)
        Soaker.Soaker(self)
        self.Connect()
        self.Main()

    def Connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(sock)
        connectMSG = []
        if self.info['SASL']:
            self.ircSend('CAP LS')
        self.ircSend('NICK %s' % self.info['NICK'])
        self.ircSend('USER %s %s %s :%s' % (self.info['NICK'], self.info['NICK'], self.info['NICK'], self.info['NAME']))
        self.ircSend('JOIN %s' % ','.join(self.info['CHAN']))

    def Main(self):
        while True:
            rawdata = self.irc.recv(4096)
            try:
                data = rawdata.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    data = rawdata.decode('cp1252')
                except UnicodeDecodeError:
                    try:
                        data = rawdata.decode('iso8859-1')
                    except:
                        continue
            lines = str(data).split('\n')
            for line in lines:
                if len(line) < 1:
                    continue

                Log = Logger.interpret(line)

                # reply to pings
                if Log['command'] == 'PING':
                    self.ircSend('PONG :%s' % Log['trail'][0])
                    continue

                # SASL
                if self.info['SASL']:
                    if Log['command'] == 'CAP':
                        if Log['parameters'] [0] == '*' and Log['parameters'][1] == 'LS':
                            self.ircSend('CAP REQ :%s' % ' '.join(Log['trail']))
                            continue
                        if Log['parameters'] [1] == 'ACK':
                            self.ircSend('AUTHENTICATE PLAIN')
                            continue
                    if Log['command'] == 'AUTHENTICATE' and Log['parameters'][0] == '+':
                        sasl_token = '\0'.join([self.info['NICK'], self.info['NICK'], self.info['PASS']])
                        self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        continue
                    if Log['command'] == '903':
                        self.ircSend('CAP END')
                        self.ircSend('JOIN %s' % ','.join(self.info['CHAN']))
                        continue

                # checks when identified with nickserv
                if Log['command'] == 'NOTICE' and Log['nick'] == 'NickServ':
                    if len(Log['trail']) > 3:
                        if 'registered' in Log['trail'][3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            continue
                        if Log['trail'][3] == 'identified':
                            self.ircSend('JOIN %s' % ','.join(self.info['CHAN']))
                            continue

                # checks for INVITE received
                if Log['command'] == 'INVITE' and Log['parameters'][0] == self.info['NICK']:
                    if Log['trail'][0] not in self.info['CHAN']:
                        self.info['CHAN'].append(Log['trail'][0])
                        self.updateFile()
                        self.ircSend('JOIN %s' % Log['trail'][0])

                # checks channel join
                if Log['command'] == 'JOIN':
                    if Log['nick'] == self.info['NICK']:
                        self.activeDict[Log['parameters'][0]] = {}
                        self.ircSend('WHO %s %%na' % Log['parameters'][0])
                    elif Log['nick'] not in self.activeDict[Log['parameters'][0]]:
                        self.activeDict[Log['parameters'][0]][Log['nick']] = 0
                        if Log['nick'] not in list(self.userDict.values()):
                            self.ircSend('WHOIS %s' % Log['nick'])
                    continue

                # checks nick change
                if Log['command'] == 'NICK':
                    if Log['nick'] == self.info['NICK']:
                        self.info['NICK'] = Log['trail'][0]
                    else:
                        for channels in self.info['CHAN']:
                            if Log['nick'] in self.activeDict[channels]:
                                self.activeDict[channels][Log['trail'][0]] = self.activeDict[channels][Log['nick']]
                                del self.activeDict[channels][Log['nick']]
                        self.ircSend('WHOIS %s' % Log['trail'][0])
                    continue

                # parses NAMES result
                if str(Log['command']) == '353' and len(Log['parameters']) > 2:
                    if Log['parameters'][-1] not in self.activeDict:
                        self.activeDict[Log['parameters'][-1]] = {}
                    for names in Log['trail']:
                        names = names.lstrip('@+')
                        if names != self.info['NICK']:
                            self.activeDict[Log['parameters'][-1]][names] = 0
                    continue

                # parses WHOIS result
                if (str(Log['command']) == '330' or str(Log['command']) == '354') and len(Log['parameters']) > 2:
                    if Log['parameters'][2] != str(0):
                        if Log['parameters'][2] not in self.userDict:
                            self.userDict[Log['parameters'][2]] = []
                        if Log['parameters'][1] not in self.userDict[Log['parameters'][2]] and Log['parameters'][1] != self.info['NICK']:
                            self.userDict[Log['parameters'][2]].append(Log['parameters'][1])
                        self.updateFile()
                    continue

                # updates active list if user leaves
                if Log['command'] == 'PART':
                    if Log['nick'] in self.activeDict[Log['parameters'][0]]:
                        del self.activeDict[Log['parameters'][0]][Log['nick']]
                    continue
                if Log['command'] == 'QUIT':
                    for channels in self.info['CHAN']:
                        if Log['nick'] in self.activeDict[channels]:
                            del self.activeDict[channels][Log['nick']]
                    continue

                # checks when PRIVMSG received
                if Log['command'] == 'PRIVMSG':
                    Log['context'] = Log['parameters'][0]
                    if Log['context'] not in self.info['UNLOAD'].keys():
                        self.info['UNLOAD'][Log['context']] = []
                    
                    # builds last spoke list
                    if Log['context'] not in self.activeDict:
                        self.activeDict[Log['context']] = {}
                    self.activeDict[Log['context']][Log['nick']] = Log['time']
                    validList = []
                    for group in self.userDict.values():
                        validList.extend(group)
                    if Log['nick'] not in validList and Log['cap'] == '+':
                        self.ircSend('WHOIS %s' % Log['nick'])

                    if Log['host'] in self.info['OWNER'] + self.info['SUDOER']:
                        if len(Log['trail']) > 1:
                            def imports():
                                for name, val in globals().items():
                                    if isinstance(val, types.ModuleType):
                                        yield val.__name__
                            try:
                                if Log['trail'][0].lower() == '!load':
                                    if Log['trail'][1] in self.info['UNLOAD'][Log['context']]:
                                        self.info['UNLOAD'][Log['context']].remove(Log['trail'][1])
                                        self.PRIVMSG(Log['context'],'Module \'%s\' loaded' % Log['trail'][1])
                                        
                                if Log['trail'][0].lower() == '!unload':
                                    if Log['trail'][1] in list(imports()) and Log['trail'][1] not in self.info['UNLOAD'][Log['context']]:
                                        self.info['UNLOAD'][Log['context']].append(Log['trail'][1])
                                        self.PRIVMSG(Log['context'],'Module \'%s\' unloaded' % Log['trail'][1])
                                        self.updateFile()

                                if Log['trail'][0].lower() == '!reload':
                                    module = __import__(Log['trail'][1])
                                    if Log['trail'][1] == 'IRCbot':
                                        self.ircSend('QUIT')
                                    if Log['trail'][1] in list(imports()):
                                        importlib.reload(module)
                                        self.PRIVMSG(Log['context'],'Module \'%s\' reloaded' % Log['trail'][1])
                            except Exception as e:
                                print(e)

                        if Log['trail'][0] == '!quit':
                            self.ircSend('QUIT')
                            sys.exit('User exited')

                    if 'Soaker' not in self.info['UNLOAD'][Log['context']]:
                        Soaker.Handler(self, Log)
                        
                    if 'Commands' not in self.info['UNLOAD'][Log['context']]:
                        Commands.Handler(self, Log)
                    
                    if 'URLInfo' not in self.info['UNLOAD'][Log['context']]:
                        URLInfo.Handler(self, Log)

    def updateFile(self):
        with open('nwobot.conf', 'r') as file:
            oldConf = eval(file.read())
        with open('users', 'r') as file:
            oldUser = eval(file.read())
        if self.info != oldConf:
            with open('nwobot.conf', 'w+') as file:
                file.write(str(self.info))
        if self.userDict != oldUser:
            with open('users', 'w+') as file:
                file.write(str(self.userDict))

    def listActive(self, chan, minutes = 10, caller = None, full = False, exclude = []):
        activeList = []
        validList = []
        timenow = time.time()
        userDict = list(self.userDict)
        mostRecent = list(dict(sorted(self.activeDict[chan].items(), key = itemgetter(1), reverse = True)).keys())
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
            if key not in self.info['IGNORE'] and key != self.info['NICK'] and key not in exclude and (timenow - self.activeDict[chan][key] <= minutes * 60 or full):
                    activeList.append(key)
        return activeList

    def PRIVMSG(self, context, message):
        self.ircSend('PRIVMSG %s :%s' % (context, message))

    def ircSend(self, message):
        print('%s %s' % (time.strftime('%H:%M:%S', time.gmtime(time.time())), message))
        self.irc.send(bytes('%s\r\n' % message, 'UTF-8'))

IRC()
