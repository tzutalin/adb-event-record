#!/usr/bin/python

'''
Copyright 2016-Present, Tzutalin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import argparse
import re
import locale
import subprocess
from subprocess import PIPE
import sys
import os
import time

__version__ = '1.0.1'

EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
STORE_LINE_RE = re.compile(r"(\S+) (\S+) (\S+) (\S+) (\S+)$")

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def dlog(msg):
    print(str(msg))

def ilog(msg):
    print(Colors.OKBLUE + str(msg) + Colors.ENDC)

def elog(msg):
    print(Colors.FAIL + str(msg) + Colors.ENDC)

class AdbEventRecorder(object):
    def __init__(self, adb):
        self.adb_command = adb
        self.adb_shell_command = adb + ['shell']

    def push(self, src, dst):
        if subprocess.call(self.adb_command + ['push', src, dst]) != 0:
            raise OSError('push failed')

    def goToActivity(self, activity):
        ilog('Go to the activity:' + activity)
        if subprocess.call(self.adb_shell_command + ['am', 'start', '-a', activity]) != 0:
            raise OSError('push failed')

    def checkPermission(self):
        ilog('Checking permission')
        if subprocess.call(self.adb_command + ['root']) != 0:
            raise OSError('Insufficient permissions')

    def listAllEvent(self):
        ilog('List all events')
        adb = subprocess.Popen(self.adb_shell_command + ['getevent', '-i'], stdin=PIPE, stdout=PIPE,
                               stderr=PIPE, shell=True)
        while adb.poll() is None:
            try:
                line = adb.stdout.readline().decode('utf-8', 'replace').strip()
                if len(line) != 0:
                    dlog(line)
            except KeyboardInterrupt:
                break

    def displayAllEvents(self):
        adb = subprocess.Popen(self.adb_shell_command + ['getevent', '-r', '-q'], stdin=PIPE, stdout=PIPE,
                               stderr=PIPE)

        while adb.poll() is None:
            try:
                millis = int(round(time.time() * 1000))
                line = adb.stdout.readline().decode('utf-8', 'replace').strip()
                if len(line) != 0:
                    dlog("{} {}".format(millis, line))
            except KeyboardInterrupt:
                break
            if len(line) == 0:
                break

    def record(self, fpath, eventNum=None):
        ilog('Start recording')
        record_command = self.adb_shell_command + ['getevent']
        adb = subprocess.Popen(record_command,
                               stdin=PIPE, stdout=PIPE,
                               stderr=PIPE)

        outputFile = open(fpath, 'w')
        while adb.poll() is None:
            try:
                millis = int(round(time.time() * 1000))
                line = adb.stdout.readline().decode('utf-8', 'replace').strip()
                match = EVENT_LINE_RE.match(line.strip())
                if match is not None:
                    dev, etype, ecode, data = match.groups()
                    ## Filter event
                    if eventNum is not None and '/dev/input/event%s' % (eventNum) != dev:
                        continue
                    ## Write to the file
                    etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                    rline = "%s %s %s %s %s\n" % (millis, dev, etype, ecode, data)
                    dlog(rline)
                    outputFile.write(rline)
            except KeyboardInterrupt:
                break
            if len(line) == 0:
                break
        outputFile.close()
        ilog('End recording')

    def play(self, fpath, repeat=False):
        ilog('Start playing')
        while True:
            lastTs = None
            with open(fpath) as fp:
                for line in fp:
                    match = STORE_LINE_RE.match(line.strip())
                    ts, dev, etype, ecode, data = match.groups()
                    ts = float(ts)
                    if lastTs and (ts - lastTs) > 0:
                        delta_second = (ts - lastTs) / 1000
                        time.sleep(delta_second)

                    lastTs = ts
                    cmds = self.adb_shell_command + ['sendevent', dev, etype, ecode, data]
                    dlog(cmds)
                    if subprocess.call(cmds) != 0:
                        raise OSError('sendevent failed')

            if repeat == False:
                break
        ilog('End playing')

def main(*args):
    parser = argparse.ArgumentParser(
        description='Record events from an Android device')
    parser.add_argument('-e', '--adb', metavar='COMMAND', default='adb', type=str,
                        help='Use the given adb binary and arguments.')
    parser.add_argument('--device', action='store_true',
                        help='Directs command to the only connected USB device; ' +
                             'returns an error if more than one USB device is ' +
                             'present. ' +
                             'Corresponds to the "-d" option of adb.')
    parser.add_argument('--repeat', action='store_true',
                        help='Repeat to play the events.')
    parser.add_argument('--show', action='store_true',
                        help='Show all of the events from the device')
    parser.add_argument('-n', '--event', type=str,
                        help='The event number, n, to record /dev/input/event[n]')
    parser.add_argument('-r', '--record', type=str,
                        help='Store the record data to the file')
    parser.add_argument('-p', '--play', type=str,
                        help='Play the record data')
    parser.add_argument('--activity', type=str,
                        help='Go the activity when play the record events')

    args = parser.parse_args()
    adb = args.adb.split(' ')
    if args.device:
        adb += ['-d']

    adb_recorder = AdbEventRecorder(adb)
    adb_recorder.listAllEvent()
    if args.record:
        adb_recorder.checkPermission()
        adb_recorder.record(args.record, args.event)
    elif args.play and os.path.exists(args.play):
        if args.activity:
            adb_recorder.goToActivity(args.activity)
        adb_recorder.play(args.play, args.repeat)
    elif args.show:
        adb_recorder.checkPermission()
        adb_recorder.displayAllEvents()
    else:
        elog('Add -r [Path] to record')
        elog('Add -p [Path] to play')

if __name__ == '__main__':
    main(*sys.argv)
