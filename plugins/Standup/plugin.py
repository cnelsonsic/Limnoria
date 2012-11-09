###
# Copyright (c) 2002-2004, Jeremiah Fincher
# Copyright (c) 2009-2010, James Vega
# Copyright (c) 2012, Charles Nelson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import datetime
import supybot.conf as conf
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
from supybot.commands import wrap, many
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('Standup')

class FakeLog(object):
    def flush(self):
        return
    def close(self):
        return
    def write(self, s):
        return

class Standup(callbacks.Plugin):
    '''This plugin manages standup meetings, both synchronous and async.
    You can tell it what you did yesterday by using the "yesterday" command.
    You can tell it what you plan on doing today by using the "today" command.
    If you have blockers, you can use the "blockers" command.
    To find out what everyone's said so far, use "summary".
    '''
    noIgnore = True
    def __init__(self, irc):
        self.__parent = super(Standup, self)
        self.__parent.__init__(irc)
        self.tasks = {}

    def handle_task(self, irc, msg, work, command):
        if msg.nick not in self.tasks:
            self.tasks[msg.nick] = {}
        self.tasks[msg.nick][command] = ' '.join(work)
        if 'yesterday' not in self.tasks[msg.nick]:
            irc.reply("{name}: What did you do yesterday?".format(name=msg.nick))
        if 'today' not in self.tasks[msg.nick]:
            irc.reply("{name}: What are you going to do today?".format(name=msg.nick))

    def today(self, irc, msg, args, work):
        self.handle_task(irc, msg, work, 'today')
    today = wrap(today, [many('anything')])

    def yesterday(self, irc, msg, args, work):
        self.handle_task(irc, msg, work, 'yesterday')
    yesterday = wrap(yesterday, [many('anything')])

    def summary(self, irc, msg, args):
        '''Show a summary of things people have said they worked on or will work on.'''
        date = datetime.datetime.now().strftime("%c")
        irc.reply("Here's a summary as of {date}.".format(date=date))
        for person, tasks in self.tasks.iteritems():
            for task in ('yesterday', 'today'):
                message = '{person} said, "{command} {task}"'.format(person=person, command=task.title(), task=tasks[task])
                irc.reply(message)
    summary = wrap(summary)

    def doJoin(self, irc, msg):
        for channel in msg.args[0].split(','):
            if(self.registryValue('async', channel)):
                # Tell people what they've missed.
                pass


Class = Standup
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
