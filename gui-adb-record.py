#!/usr/bin/env python

import argparse
import sys
import os
import Tkinter as tk
import Tkinter
import Tkconstants
import tkFileDialog

from adbrecord import AdbEventRecorder
'''
Copyright 2016, Tzutalin

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

__version__ = '0.0.1'


class FileDialog(Tkinter.Frame):

    def __init__(self, root, dir, textView):
        Tkinter.Frame.__init__(self, root)
        button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        Tkinter.Button(self, text='Open Dir',
                       command=self.askForDir).pack(**button_opt)
        Tkinter.Button(self, text='Play record data',
                       command=self.playRecordData).pack(**button_opt)
        Tkinter.Button(self, text='Record data',
                       command=self.recordData).pack(**button_opt)

        self.recFile = ''
        self.dir = dir
        self.adbrecord = AdbEventRecorder([b'adb'])
        self.dir_opt = options = {}
        self.file_opt = options = {}
        self.textView = textView
        options['defaultextension'] = '.log'
        options['filetypes'] = [('all files', '.*')]
        options['initialdir'] = self.dir
        options['parent'] = root
        options['title'] = 'adb-record'
        self.textView.insert('end', 'Open %s\n' % (self.dir))

    def askForDir(self):
        """Returns a selected directoryname."""
        self.dir = tkFileDialog.askdirectory(**self.dir_opt)
        self.textView.insert('end', 'Open %s\n' % (self.dir))

    def playRecordData(self):
        self.recFile = tkFileDialog.askopenfilename(**self.file_opt)
        if os.path.exists(self.recFile):
            print 'play' + self.recFile
            self.adbrecord.play(self.recFile, True)
        else:
            print 'Cannot find ' + self.recFile

    def recordData(self):
        if os.path.exists(self.dir):
            self.recFile = self.getNewFileName()
            self.textView.insert('end', 'recording to ' + os.path.join(self.dir, self.recFile) + '\n')
            self.adbrecord.record(self.recFile, 4)
        else:
            print 'Not exists ' + self.dir

    def getNewFileName(self):
        fileName = 'record.log'
        count = 1
        # Find the name which is not used before
        while os.path.exists(os.path.join(self.dir, fileName)):
            fileName = fileName + str(count)
            count = count + 1

        return fileName

def main(*args):
    parser = argparse.ArgumentParser(
        description='Record android events like touch event')
    parser.add_argument('-d', '--dir', default='.', type=str,
                        help='The record data dir')

    args = parser.parse_args()
    root = tk.Tk()
    textView = tk.Text(root, background='black',
                        foreground='white', font=('Comic Sans MS', 12))
    textView.pack()
    FileDialog(root, args.dir, textView).pack()
    root.mainloop()


if __name__ == '__main__':
    main(*sys.argv)
