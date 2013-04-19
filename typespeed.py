#!/usr/bin/env python2.7


# Jorge Niedbalski <jnr@pyrosome.org>
#
#  [ Typespeed bot ]
#
#  * apt-get install python-virtkey
#  * pip install python-ptrace
#  * Run typespeed
#  * Wait for words start entering to the console (left-to-right), focus your mouse on the terminal
#  * Profit


from ptrace.debugger import PtraceDebugger
from ptrace.func_call import FunctionCallOptions
from optparse import OptionParser

import gtk
import virtkey
import sys
import subprocess
import re
import time

enter_key = gtk.gdk.keyval_from_name("KP_Enter")
options = None

def get_options():
    parser = OptionParser()
    parser.add_option("-d", "--dictionary", dest="dict",
                      help="Specify dicctionary: unix",
                      default="unix")

    (options, args) = parser.parse_args()
    return options

def get_words():
    global options
    path = "/usr/share/typespeed/words/words.%s" % options.dict
    with open(path) as reader:
        readed = reader.read()
    return readed.splitlines()

def op_syscall(process):

    state = process.syscall_state
    syscall = state.event(FunctionCallOptions())

    words = get_words()

    if syscall.name == 'write':
        co = re.sub(r'(\\x.*?m)', '', syscall.format())
        matched = re.match(r".*\,(.*)\,.*", co)

        if matched:
            cleanup = re.sub(r'(\\r|\'|\\n)+', '', matched.group(1))

            if cleanup:
                splitted = cleanup.split(" ")
                for word in words:
                    for captured in splitted:
                        if captured.startswith(word):
                            v = virtkey.virtkey()

                            for key in word:
                                key_value = gtk.gdk.keyval_from_name(key)
                                v.press_unicode(key_value)
                                v.release_unicode(key_value)

                            v.press_keysym(enter_key)
                            v.release_keysym(enter_key)
    process.syscall()

def main():
    global options
    options = get_options()

    dbg = PtraceDebugger()
    pid = int(subprocess.check_output(['pidof', "typespeed"]))

    process = dbg.addProcess(pid, False)
    process.syscall()

    while True:
        event = dbg.waitSyscall()
        process = event.process 
        op_syscall(process)

    dbg.quit()


if __name__ == "__main__":
    main()
