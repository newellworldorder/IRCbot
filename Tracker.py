# coding=utf8

def Handler(self,line):
    # checks nick change
    if line['command'] == 'NICK':
        if line['nick'] == self.info['NICK']:
            self.info['NICK'] = line['trail'][0]
        else:
            for channel in self.info['CHAN']:
                if self.lastSeen[channel][line['nick']]:
                    self.lastSeen[channel][line['trail'][0]] = self.lastSeen[channel][line['nick']]
                    self.lastSeen[channel][line['nick']] = line['trail'][0]
            self.updateLastSeen()
        return True

    # checks channel join
    if line['command'] == 'JOIN':
        if line['nick'] == self.info['NICK']:
            self.info['CHAN'].append(line['context'])
        else:
            self.lastSeen[line['context']][line['nick']] = [line['time'], 'join', None]
            self.updateLastSeen()
        return True

    # updates active list if user leaves
    if line['command'] == 'PART':
        if line['nick'] == self.info['NICK']:
            self.info['CHAN'].remove(line['context'])
        else:
            self.lastSeen[line['context']][line['nick']] = [line['time'], 'leav', ' '.join(line['trail']).encode('utf-8')]
        self.updateLastSeen()
        return True

    # updates active list if user quits
    if line['command'] == 'QUIT':
        for channel in self.lastSeen:
            self.lastSeen[channel][line['nick']] = [line['time'], 'quitt', ' '.join(line['trail']).encode('utf-8')]
        self.updateLastSeen()
        return True

    if line['command'] == 'KICK':
        if line['nick'] == self.info['NICK']:
            self.info['CHAN'].remove(line['context'])
        else:
            self.lastSeen[line['context']][line['nick']] = [line['time'], 'kicked by %s' % line['nick'], ' '.join(line['trail']).encode('utf-8')]
        self.updateLastSeen()
        return True

    return False
