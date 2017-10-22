# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import datetime
import sys
import time

from multiprocessing import Queue  # hack

import common

class cmd_log:
  def log(self, message, info = False):
    print(message, file = sys.stdout if info else sys.stderr)

  def log_ln(self, message, info = False):
    self.log(message.rstrip('\r\n'), info)

  def log_ts(self, message, info = False):
    self.log_ln('{}: {}'.format(datetime.datetime.fromtimestamp(int(time.time())), message), info)

class cmd_app:
  def __init__(self):
    self.log      = cmd_log()

  def run(self):
    env = common.load_env(self.log)
    if env['game_dir'] is None:
      return
    ca_bundle_path = common.locate_ca_bundle(env['script_dir'])
    if ca_bundle_path is None:
      common.get_node({'src': 'https://curl.haxx.se/ca/cacert.pem', 'dest': 'cacert.pem'}, False, False, env['script_dir'], self.log)
      self.log.log_ts('CA Bundle updated', info = True)
    addons = common.list_addons(env, self.log)
    update_context = {'launch': True, 'error': False}
    common.update_addons(env, addons, self.log, False, update_context)
    if update_context['error']:
      pass
    elif update_context['launch']:
      common.launch(env['game_dir'], env['game_args'])

a = cmd_app()
a.run()
