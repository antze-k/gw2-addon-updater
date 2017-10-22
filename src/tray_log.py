# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import copy
import datetime
import os
import threading
import time
import win32con
import win32gui

import common

def threaded_function(thread_data, thread_static):
  while not thread_data.stop:
    update_hwnd = None
    with thread_static.lock:
      if thread_static.queue:
        thread_static.memlog.extend(thread_static.queue)
        #for message in thread_static.queue:
        #  with open('gw2-addon-updater.log', 'a') as logfile:
        #    logfile.write('{}\n'.format(message))
        del thread_static.queue[:]
        if len(thread_static.memlog) > thread_static.memmax:
          del thread_static.memlog[:(len(thread_static.memlog)-thread_static.memmax)]
        update_hwnd = thread_static.hWnd
    if update_hwnd is not None:
      win32gui.SendMessage(update_hwnd, win32con.WM_COMMAND, common.commands.UPDATE_LOG, 0)
    time.sleep(0.01)

class thread_data_type:
  stop = False

class thread_static_type:
  lock    = threading.Lock()
  queue   = []
  memlog  = []
  memmax  = 1000
  hWnd    = None

class log:
  thread        = None
  thread_data   = None
  thread_static = thread_static_type()

  def start(self):
    if self.thread is not None: return
    self.thread_data = thread_data_type()
    self.thread = threading.Thread(name = 'MemLogThread', target = threaded_function, args = (self.thread_data, self.thread_static))
    self.thread.start()

  def stop(self):
    if self.thread is None: return
    if self.thread_data is None: return
    self.thread_data.stop = True
    self.thread = None

  def bind_hwnd(self, hWnd):
    with self.thread_static.lock:
      self.thread_static.hWnd = hWnd

  def log(self, message, info = False):
    with self.thread_static.lock:
      self.thread_static.queue.append(message)

  def log_ln(self, message, info = False):
    self.log(message.rstrip('\r\n'))

  def log_ts(self, message, info = False):
    self.log_ln('{}: {}'.format(datetime.datetime.fromtimestamp(int(time.time())), message))

  def extract(self):
    with self.thread_static.lock:
      log = copy.deepcopy(self.thread_static.memlog)
    return log
