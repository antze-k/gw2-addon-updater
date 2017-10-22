# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import os
import requests
import threading
import time
import sys
import win32con
import win32gui

import common

def threaded_function(thread_data, thread_static, env, addons, hWnd, log):
  while not thread_data.stop:
    time.sleep(0.01)
    will_update_ca_bundle = False
    will_update_addons    = False
    force_update_addons   = False
    activate_launch       = False
    with thread_static.lock:
      if thread_static.need_update_ca_bundle:
        will_update_ca_bundle = common.locate_ca_bundle(env['script_dir']) is None or thread_static.force_update_ca_bundle
        thread_static.need_update_ca_bundle   = False
        thread_static.force_update_ca_bundle = False
      if thread_static.need_update_addons:
        will_update_addons = True
        force_update_addons = thread_static.force_update_addons
        thread_static.need_update_addons  = False
        thread_static.force_update_addons = False
      activate_launch = thread_static.queue_launch
      thread_static.queue_launch = False
    if will_update_ca_bundle:
      try:
        common.get_node({'src': 'https://curl.haxx.se/ca/cacert.pem', 'dest': 'cacert.pem'}, False, False, env['script_dir'], log)
        log.log_ts('CA Bundle updated', info = True)
      except:
        exc = sys.exc_info()
        log.log_ts('{}: {}'.format(exc[0], exc[1]))
        win32gui.SendMessage(hWnd, win32con.WM_COMMAND, common.commands.SHOW_LOG, 0)
        continue
    if will_update_addons:
      update_context = {'launch': activate_launch, 'error': False}
      common.update_addons(env, addons, log, force_update_addons, update_context)
      if update_context['error']:
        win32gui.SendMessage(hWnd, win32con.WM_COMMAND, common.commands.SHOW_LOG, 0)
      elif update_context['launch']:
        win32gui.SendMessage(hWnd, win32con.WM_COMMAND, common.commands.LAUNCH, 0)

class thread_data_type:
  stop = False

class thread_static_type:
  lock                    = threading.Lock()
  need_update_ca_bundle   = True
  force_update_ca_bundle  = False
  need_update_addons      = False
  force_update_addons     = False
  queue_launch            = False

class updater_thread:
  thread        = None
  thread_data   = None
  thread_static = thread_static_type()

  def start(self, env, hWnd, log):
    if self.thread is not None: return
    self.thread_data = thread_data_type()
    self.thread = threading.Thread(name = 'UpdaterThread', target = threaded_function, args = (self.thread_data, self.thread_static, env, common.list_addons(env, log), hWnd, log))
    self.thread.start()

  def stop(self):
    if self.thread is None: return
    if self.thread_data is None: return
    self.thread_data.stop = True
    self.thread = None

  def update_launch(self):
    with self.thread_static.lock:
      self.thread_static.need_update_addons = True
      self.thread_static.queue_launch       = True

  def update(self):
    with self.thread_static.lock:
      self.thread_static.need_update_addons = True

  def force_update(self):
    with self.thread_static.lock:
      self.thread_static.need_update_addons = True
      self.thread_static.force_update_addons = True

  def force_update_ca_bundle(self):
    with self.thread_static.lock:
      self.thread_static.need_update_ca_bundle = True
      self.thread_static.force_update_ca_bundle = True
