###
# Copyright (c) 2004, Jeremiah Fincher
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

"""
Defends a channel against actions by people who don't have the proper
capabilities.
"""

import supybot

__revision__ = "$Id$"
__author__ = supybot.authors.jemfinch
__contributors__ = {}


import supybot.conf as conf
import supybot.utils as utils
import supybot.plugins as plugins
import supybot.privmsgs as privmsgs
import supybot.registry as registry
import supybot.callbacks as callbacks


def configure(advanced):
    # This will be called by setup.py to configure this module.  Advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Protector', True)

Protector = conf.registerPlugin('Protector')
conf.registerChannelValue(Protector, 'enable',
    registry.Boolean(True, """Determines whether this plugin is enabled in a
    given channel."""))
conf.registerChannelValue(Protector, 'takeRevenge',
    registry.Boolean(True, """Determines whether the bot will take revenge on
    people who do things it doesn't like (somewhat like 'bitch mode' in other
    IRC bots)."""))
conf.registerChannelValue(Protector.takeRevenge, 'onOps',
    registry.Boolean(False, """Determines whether the bot will take revenge
    even on ops (people with the #channel,op capability) who violate the
    channel configuration."""))

class ImmuneNicks(conf.ValidNicks):
    List = ircutils.IrcSet

conf.registerChannelValue(Protector, 'immune',
    ImmuneNicks([], """Determines what nicks the bot will consider to
    be immune from enforcement.  These nicks will not even have their actions
    watched by this plugin.  In general, only the ChanServ for this network
    will be in this list."""))

class Protector(callbacks.Privmsg):
    def isImmune(self, irc, msg):
        if not ircutils.isUserHostmask(msg.prefix):
            self.log.debug('%r is immune, it\'s a server.', msg)
            return True # It's a server prefix.
        if ircutils.strEqual(msg.nick, irc.nick):
            self.log.debug('%r is immune, it\'s me.', msg)
            return True # It's the bot itself.
        if msg.nick in self.registryValue('immune', msg.args[0]):
            self.log.debug('%r is immune, it\'s configured to be immune.', msg)
            return True
        return False

    def isOp(self, irc, channel, hostmask):
        cap = ircdb.makeChannelCapability(channel, 'op')
        if ircdb.checkCapability(hostmask, cap):
            self.log.debug('%s is an op on %s, it has %s.',
                           hostmask, channel, cap)
            return True
        return False
        
    def isProtected(self, irc, channel, hostmask):
        cap = ircdb.makeChannelCapability(channel, 'protected')
        if ircdb.checkCapability(msg.prefix, cap):
            self.log.debug('%s is protected on %s, it has %s.',
                           hostmask, channel, cap)
            return True
        return False

    def takeRevenge(self, irc, msg, reason):
        pass

    def __call__(self, irc, msg):
        if not msg.args:
            self.log.debug('Ignoring %r, no msg.args.', msg, irc)
        elif not ircutils.isChannel(msg.args[0]):
            self.log.debug('Ignoring %r, not on a channel.', msg)
        elif msg.args[0] not in irc.state.channels:
            # One has to wonder how this would happen, but just in case...
            self.log.debug('Ignoring %r, bot isn\'t in channel.', msg)
        elif irc.nick not in irc.state.channels[msg.args[0]].ops:
            self.log.debug('Ignoring %r, bot is not opped.', msg)
        elif self.isImmune(irc, msg):
            self.log.debug('Ignoring %r, it is immune.', msg, irc)
        else:
            super(Protector, self).__call__(irc, msg)

    def doMode(self, irc, msg):
        pass

    def doKick(self, irc, msg):
        channel = msg.args[0]
        kicked = msg.args[1].split(',')
        protected = []
        for nick in kicked:
            if ircutils.strEqual(nick, irc.nick):
                irc.queueMsg(ircmsgs.join(channel))
                return # We can't revenge because we won't have ops on rejoin.
            hostmask = irc.state.nickToHostmask(nick)
            if self.isProtected(channel, hostmask):
                self.log.info('%s was kicked from %s and is protected; '
                              'inviting back.', hostmask, channel)
                irc.queueMsg(ircmsgs.invite(nick, channel))
                protected.append(nick)
        if protected:
            self.takeRevenge(irc, msg, '%s %s protected.' %
                                       (utils.commaAndify(protected),
                                        utils.be(len(protected))))
            

Class = Protector

# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78: