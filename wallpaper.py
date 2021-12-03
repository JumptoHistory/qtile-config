# Copyright (c) 2015 Muhammed Abuali
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# To use this widget, you will need to install feh wallpaper changer

import os
import random
import subprocess
import threading
import time

from libqtile import bar, hook, qtile
from libqtile.log_utils import logger
from libqtile.widget import base


class Wallpaper(base._TextBox):
    defaults = [
        ("directory", "~/Pictures/wallpapers/", "Wallpaper Directory"),
        ("wallpaper", None, "Wallpaper"),
        ("wallpaper_command", ['feh', '--bg-fill'], "Wallpaper command. If None, the"
            "wallpaper will be painted without the use of a helper."),
        ("random_selection", False, "If set, use random initial wallpaper and "
         "randomly cycle through the wallpapers."),
        ("label", None, "Use a fixed label instead of image name."),
        ("option", "fill", "How to fit the wallpaper when wallpaper_command is"
            "None. None, 'fill' or 'stretch'."),
        ("timeout", 0, "Time in seconds till it automatically cycles to the next picture. Set it to 0 to disable it."),
        ("max_width", None, "maximum number of characters to display "
            "(None for all, useful when width is bar.STRETCH)"),
    ]

    def __init__(self, **config):
        base._TextBox.__init__(self, 'empty', width=bar.CALCULATED, **config)
        self.add_defaults(Wallpaper.defaults)
        self.index = 0
        self.images = []
        self.get_wallpapers()
        if self.random_selection:  # Random selection after reading all files
            self.index = random.randint(0, len(self.images) - 1)

        self.add_callbacks({
            'Button1': self.set_wallpaper,
            'Button2': lambda: self.set_wallpaper(backward = True),
            'Button3': self.copy_filename,
            })

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        if not self.bar.screen.wallpaper:
            self.set_wallpaper()

        if self.timeout > 0:
            #self.timer = threading.Timer(self.timeout, self.timer_cycle)
            #self.timer.start()
            self.timer = threading.Thread(target=self.timer_cycle)
            self.timer.daemon = True
            self.timer.start()

    def get_path(self, file):
        return os.path.join(os.path.expanduser(self.directory), file)

    def get_wallpapers(self):
        try:
            # get path of all files in the directory
            self.images = list(
                filter(os.path.isfile,
                       map(self.get_path,
                           os.listdir(
                               os.path.expanduser(self.directory)))))
        except IOError as e:
            logger.exception("I/O error(%s): %s", e.errno, e.strerror)

    def set_wallpaper(self, backward = False):
        prev = self.index
        if backward:
            self.index = self.prev
        elif self.random_selection:
            self.index = random.randint(0, len(self.images) - 1)
        else:
            self.index += 1
            self.index %= len(self.images)
        self.prev = prev
        if len(self.images) == 0:
            if self.wallpaper is None:
                self.text = "empty"
                return
            else:
                self.images.append(self.wallpaper)
        cur_image = self.images[self.index]
        if self.label is None:
            self.text = os.path.basename(cur_image)
        else:
            self.text = self.label

        if self.wallpaper_command:
            self.wallpaper_command.append(cur_image)
            subprocess.call(self.wallpaper_command)
            self.wallpaper_command.pop()
        else:
            self.qtile.paint_screen(self.bar.screen, cur_image, self.option)
        self.trim_text()
        self.bar.draw()

    def timer_cycle(self):
        #self.timer = threading.Timer(self.timeout, self.timer_cycle)
        #self.timer.start()
        while True:
            time.sleep(self.timeout)
            self.set_wallpaper()

    def trim_text(self):
        text = self.text.strip()
        if self.max_width is not None and len(text) > self.max_width:
            text = text[:self.max_width] + "..."

        self.text = text

    def copy_filename(self):
        qtile.cmd_spawn('sh -c \'echo ' + os.path.basename(self.images[self.index]) + '| xclip -in -selection clipboard\'')

