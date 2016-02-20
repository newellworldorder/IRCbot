# coding=utf8

import base64, Commands, Config, importlib, Logger, socket, ssl, sys, time, Tracker, types, URLInfo

class IRC:
    def __init__(self):
        Config.config(self)
        self.authed = False
        self.commandLog = []
        # lastSeen is a dict of dicts. The first level is channels, then nicks, then [time,lastAction,lastMessage]
        for channel in self.info['CHAN']:
            if channel not in self.lastSeen:
                self.lastSeen[channel] = {}
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
            for l in lines:
                if len(l) < 1:
                    continue

                line = Logger.interpret(self.info,l)

                # reply to pings
                if line['command'] == 'PING':
                    self.ircSend('PONG :%s' % line['trail'][0])
                    continue

                # SASL
                if self.info['SASL']:
                    if line['command'] == 'CAP':
                        if line['parameters'] [0] == '*' and line['parameters'][1] == 'LS':
                            self.ircSend('CAP REQ :%s' % ' '.join(line['trail']))
                            continue
                        if line['parameters'] [1] == 'ACK':
                            self.ircSend('AUTHENTICATE PLAIN')
                            continue
                    if line['command'] == 'AUTHENTICATE' and line['parameters'][0] == '+':
                        sasl_token = '\0'.join([self.info['NICK'], self.info['NICK'], self.info['PASS']])
                        self.ircSend('AUTHENTICATE %s' % base64.b64encode(sasl_token.encode('utf-8')).decode('utf-8'))
                        continue
                    if line['command'] == '903':
                        self.ircSend('CAP END')
                        self.ircSend('JOIN %s' % ','.join(self.info['CHAN']))
                        continue

                # checks when identified with nickserv
                if line['command'] == 'NOTICE' and line['nick'] == 'NickServ':
                    if len(line['trail']) > 3:
                        if 'registered' in line['trail'][3]:
                            self.ircSend('PRIVMSG NickServ :identify %s' % self.info['PASS'])
                            self.authed = True;
                            continue
                        if self.authed == True:
                            self.ircSend('JOIN %s' % ','.join(self.info['CHAN']))
                            continue

                # checks for INVITE received
                if line['command'] == 'INVITE' and line['parameters'][0] == self.info['NICK']:
                    if line['trail'][0] not in self.info['CHAN']:
                        self.info['CHAN'].append(line['trail'][0])
                        self.updateFile()
                        self.ircSend('JOIN %s' % line['trail'][0])

                if Tracker.Handler(self, line):
                    continue

                # checks when PRIVMSG received
                if line['command'] == 'PRIVMSG' and line['trail']:
                    if line['parameters'][0].lower() == self.info['NICK'].lower() and line['trail'][0] == '\001VERSION\001':
                        self.ircSend('NOTICE %s :\001VERSION MarcoRoboto:6.9:Micucksoft Winblows 10\001' % line['nick'])
                        continue

                    # builds last spoke list
                    if line['context'] not in self.lastSeen:
                        self.lastSeen[line['context']] = {}
                    self.lastSeen[line['context']][line['nick']] = [line['time'], 'talk', ' '.join(line['trail']).encode('utf-8')]
                    self.updateLastSeen()

                    try:
                        if line['host'] in self.info['OWNER'] + self.info['SUDOER']:
                            def imports():
                                for name, val in globals().items():
                                    if isinstance(val, types.ModuleType):
                                        yield val.__name__
                            if line['trail'][0] == '@reload' and line['trail'][1] in list(imports()):
                                importlib.reload(sys.modules[line['trail'][1]])
                            if line['trail'][0] == '@do':
                                self.ircSend(' '.join(line['trail'][1:]))
                            if line['trail'][0] == '@quit':
                                self.ircSend('QUIT')
                                self.irc.close()
                                sys.exit('User exited')

                        if line['nick'].lower() not in [x.lower() for x in self.info['IGNORE']]:
                            Commands.Handler(self, line)
                            URLInfo.Handler(self, line)
                    except Exception as e:
                        print(e)

    def updateFile(self):
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

    def PRIVMSG(self, context, message):
        self.ircSend('PRIVMSG %s :%s' % (context, message))

    def ircSend(self, message):
        print('%s %s' % (time.strftime('%H:%M:%S', time.gmtime(time.time())), message))
        self.irc.send(bytes('%s\r\n' % message, 'UTF-8'))

IRC()
