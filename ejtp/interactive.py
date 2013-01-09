#!/usr/bin/env python

'''
This file is part of the Python EJTP library.

The Python EJTP library is free software: you can redistribute it 
and/or modify it under the terms of the GNU Lesser Public License as
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

the Python EJTP library is distributed in the hope that it will be 
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser Public License for more details.

You should have received a copy of the GNU Lesser Public License
along with the Python EJTP library.  If not, see 
<http://www.gnu.org/licenses/>.
'''

import datetime
import json

from router import Router
from client import Client
from util   import hasher

commands = (
    'messages',
    'send',
    'set client',
    'log',
    'clear log',
    'eval',
    'quit',
)

class Interactive(object):
    def __init__(self, router=None):
        self.router = router or Router()
        self.router.run()
        self.client = None
        self.messages   = []
        self.encryptors = {}

    def view_messages(self, read=None):
        '''
        >>> inter = Interactive()
        >>> inter.view_messages()
            No messages.
        >>> inter.receive({'hello':'world'}, ["udp4", ["127.0.0.1", 666], "El Diablo"])
        >>> inter.view_messages() # doctest: +ELLIPSIS
            All messages:
        --------------------------------------------------------------------------------
        ["udp4", ["127.0.0.1", 666], "El Diablo"](at ...):
        {
            "hello": "world"
        }
        '''
        messages =  (read == None  and self.messages) \
             or (read == True  and self.read) \
             or (read == False and self.unread) \
             or []
        if not len(messages):
            print("    No messages.")
            return
        print("    "+self.read_type(read).capitalize()+" messages:")
        for message in messages:
            print("-"*80)
            print(message)

    def receive(self, *args, **kwargs):
        self.messages.append(ReceiveEvent(*args, **kwargs))

    def rcv_callback(self, msg, client):
        self.receive(json.loads(msg.content), msg.addr)

    def read_type(self, rt):
        '''
        Convert a True/False/None into the appropriate read filter name.
        >>> inter = Interactive()
        >>> inter.read_type(True)
        'read'
        >>> inter.read_type(False)
        'unread'
        >>> inter.read_type(None)
        'all'
        >>> inter.read_type(3) #doctest +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        TypeError: Expected bool or none, got 3
        '''
        if rt==True:
            return "read"
        elif rt==False:
            return "unread"
        elif rt==None:
            return "all"
        else:
            raise TypeError("Expected bool or none, got %r" % rt)

    def set_client(self, interface):
        self.client = Client(self.router, interface, lambda x: ['rotate', int(hasher.checksum(x),16)])
        self.client.rcv_callback = self.rcv_callback

    def scan_client(self):
        interface = self.scan(
'||| What interface do you want to use? \n\
||| Example: ["udp4", ["127.0.0.1", 5802], "stevey"]\n',
            "Client scan failed",
            json.loads
        )
        return self.set_client(interface)

    def scan_recipient(self):
        interface = self.scan(
'||| What interface do you want to send to? \n\
||| Example: ["udp4", ["127.0.0.1", 5803], "caroline"]\n',
            "Recipient scan failed",
            json.loads
        )
        return interface

    def scan_message(self):
        message = self.scan(
            '||| What message do you want to send? \n',
            "Message scan failed",
            json.loads
        )
        return message

    def scan(self, prompt, failmsg, validator):
        while True:
            try:
                response = raw_input(prompt)
                return validator(response)
            except KeyboardInterrupt:
                quit(1)
            except:
                print(failmsg)

    def repl(self):
        self.scan_client()
        def validate_command(command):
            command = command.lower()
            if command in commands:
                return command
            else:
                raise ValueError(command)
        while True:
            command = self.scan(
                '||| Enter a command [%s]\n' % " | ".join(commands),
                "That's not a command.",
                validate_command
            )
            if command == "messages":
                self.view_messages()
            elif command == "send":
                recipient = self.scan_recipient()
                message   = self.scan_message()
                self.client.write_json(recipient, message)
            elif command == "set client":
                self.scan_client()
            elif command == "log":
                print("    Router log:\n"+"-"*80)
                self.router.log_dump()
            elif command == "clear log":
                print("    Clearing router log...")
                del self.router.log[:]
                print("    Done.")
            elif command == "eval":
                print(eval(raw_input("\n")))
            elif command == "quit":
                quit()

    @property
    def read(self):
        return (m for m in self.messages if m.read)

    @property
    def unread(self):
        return (m for m in self.messages if not m.read)


class ReceiveEvent(object):
    '''
    Represents a frame that has arrived.
    '''
    def __init__(self, contents, sender=[], when=None):
        self.contents = contents
        self.sender   = sender
        self.time     = when or datetime.datetime.now()
        self.read     = False

    def reply(self, contents, client):
        pass

    def timestr(self):
        return self.time.strftime("%m/%d/%y %H:%M:%S")

    def __str__(self):
        return json.dumps(self.sender)+("(at %s):\n" % self.timestr())+json.dumps(self.contents, indent=4)

if __name__ == "__main__":
    inter = Interactive()
    inter.repl()
