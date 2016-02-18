# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from operator import itemgetter
import base64, Commands, Config, importlib, Logger, praw, re, requests, socket, ssl, sys, time, types, URLInfo

class IRC:
    def __init__(self):
        Config.config(self)

        # lastSeen is a dict of dicts. The first level is channels, then nicks, then [time,lastAction,lastMessage]
        self.lastSeen = {}
        for channel in self.info['CHAN']:
            self.lastSeen[channel] = {}
        Commands.redditAPI(self)
        self.Connect()
        self.Main()

    def Connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.info['HOST'], int(self.info['PORT'])))
        self.irc = ssl.wrap_socket(sock)
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

                # checks nick change
                if Log['command'] == 'NICK':
                    if Log['nick'] == self.info['NICK']:
                        self.info['NICK'] = Log['trail'][0]
                    else:
                        for channel in self.info['CHAN']:
                            if Log['nick'] in self.lastSeen[channel]:
                                self.lastSeen[channel][Log['trail'][0]] = self.lastSeen[channel][Log['nick']]
                                self.lastSeen[channel][Log['nick']] = Log['trail'][0]
                        self.updateLastSeen()
                    continue


                # checks channel join
                if Log['command'] == 'JOIN':
                    if Log['parameters'] and Log['nick'] != self.info['NICK']:
                        self.lastSeen[Log['context']][Log['nick']]['lastAction'] = [Log['time'], 'join']
                        if Log['nick'] not in self.lastSeen[Log['context']]:
                            self.lastSeen[Log['context']][Log['nick']]['lastMessage'] = None
                        self.updateLastSeen()
                    continue

                # updates active list if user leaves
                if Log['command'] == 'PART':
                    if Log['nick'] in self.lastSeen[Log['context']]:
                        self.lastSeen[Log['context']][Log['nick']]['lastAction'] = [Log['time'], 'leav', ' '.join(Log['trail'])]
                    self.updateLastSeen()
                    continue

                if Log['command'] == 'QUIT':
                    for channel in self.info['CHAN']:
                        if Log['nick'] in self.lastSeen[channel]:
                            self.lastSeen[Log['context']][Log['nick']]['lastAction'] = [Log['time'], 'quitt', ' '.join(Log['trail'])]
                    self.updateLastSeen()
                    continue

                # checks when PRIVMSG received
                if Log['command'] == 'PRIVMSG':
                    if Log['parameters'][0].lower() == self.info['NICK'] and Log['trail'][0] == '\001VERSION\001':
                        self.ircSend('NOTICE %s \001VERSION PyIRC:1.0:Windows\001' % Log['nick'])
                        continue

                    # builds last spoke list
                    if Log['context'] not in self.lastSeen:
                        self.lastSeen[Log['context']] = {}
                    if Log['nick'] not in self.lastSeen[Log['context']]:
                        self.lastSeen[Log['context']][Log['nick']] = {}
                    self.lastSeen[Log['context']][Log['nick']]['lastAction'] = [Log['time'], 'talk']
                    self.lastSeen[Log['context']][Log['nick']]['lastMessage'] = [Log['time'], ' '.join(Log['trail'])]
                    self.updateLastSeen()

                    if Log['host'] in self.info['OWNER'] + self.info['SUDOER']:
                        if Log['trail'][0] == '!quit':
                            self.ircSend('QUIT')
                            self.irc.close()
                            sys.exit('User exited')

                    Commands.Handler(self, Log)

                    URLInfo.Handler(self, Log)

    def updateFiles(self):
        self.updateConf()
        self.updateLastSeen()

    def updateConf(self):
        with open('nwobot.conf', 'r') as file:
            oldConf = eval(file.read())
        if self.info != oldConf:
            with open('nwobot.conf', 'w+') as file:
                file.write(str(self.info))

    def updateLastSeen(self):
        with open('lastseen.txt', 'r') as file:
            oldSeen = eval(file.read())
        if self.lastSeen != oldSeen:
            with open('lastseen.txt', 'w+') as file:
                file.write(str(self.lastSeen))

    def listActive(self, channel, timer = 10):
        return Logger.listActive(self, channel, timer)

    def PRIVMSG(self, context, message):
        self.ircSend('PRIVMSG %s :%s' % (context, message))

    def ircSend(self, message):
        print('%s %s' % (time.strftime('%H:%M:%S', time.gmtime(time.time())), message))
        self.irc.send(bytes('%s\r\n' % message, 'UTF-8'))

IRC()
