# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import configparser
import hashlib
import os
import requests
import shlex
import sys
import winreg

def load_env(log):
  env = {}
  script = sys.argv[0]
  if '/' not in script and '\\' not in script:
    script = sys.executable
  if 'python' in script:
    script = __file__
  env['script_dir']   = os.path.dirname(os.path.realpath(script))
  env['config_path']  = '{}\\gw2-addon-updater.ini'.format(env['script_dir'])
  env['config']       = configparser.ConfigParser()
  if os.path.isfile(env['config_path']):
    log.log_ts('Loading configuration from {}...'.format(env['config_path']), info = True)
    try:
      env['config'].read(env['config_path'])
    except:
      exc = sys.exc_info()
      log.log_ts('{}: {}'.format(exc[0], exc[1]))
  env['game_dir'] = None
  env['game_args'] = ''
  if env['config'].has_section('main'):
    if env['config'].has_option('main', 'gw2_dir'):
      try:
        env['game_dir'] = str(env['config'].get('main', 'gw2_dir'))
        log.log_ts('Game location: {}'.format(env['game_dir']), info = True)
      except:
        exc = sys.exc_info()
        log.log_ts('{}: {}'.format(exc[0], exc[1]))
    if env['config'].has_option('main', 'gw2_args'):
      env['game_args'] = str(env['config'].get('main', 'gw2_args'))
  if env['game_dir'] is None:
    log.log_ts('Trying to locate the game in the registry...', info = True)
    try:
      registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
      key = winreg.OpenKey(registry, 'SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Guild Wars 2', 0, winreg.KEY_READ)
      value, type = winreg.QueryValueEx(key, 'DisplayIcon')
      env['game_dir'] = os.path.dirname(os.path.realpath(value))
      if (len(env['game_dir']) < 3): raise RuntimeError('strange game dir')
      log.log_ts('Game located: {}'.format(env['game_dir']), info = True)
    except:
      env['game_dir'] = None
      exc = sys.exc_info()
      log.log_ts('{}: {}'.format(exc[0], exc[1]))
  if env['game_dir'] is None:
    for test_dir in ['C:\\Program Files\\Guild Wars 2', 'C:\\Games\\Guild Wars 2', 'D:\\Games\\Guild Wars 2']:
      log.log_ts('Trying to locate the game in {}...'.format(test_dir), info = True)
      try:
        if os.path.isfile('{}\\Gw2-64.exe'.format(test_dir)):
          env['game_dir'] = test_dir
          break
      except:
        env['game_dir'] = None
        exc = sys.exc_info()
        log.log_ts('{}: {}'.format(exc[0], exc[1]))
  if env['game_dir'] is None:
    log.log_ts('Cannot locate Guild Wars 2')
  return env

def parse_rule(s):
  rule = list(map(lambda x: x.strip(), s.split('->')))
  if len(rule[0]) == 0 or len(rule[1]) == 0: raise RuntimeError('invalid rule {}'.format(config.get(section, 'main')))
  return {'src': rule[0], 'dest': rule[1]}

def list_addons(env, log):
  addons = []
  try:
    config = env['config']
    for section in config.sections():
      if not config.has_option(section, 'main'): continue
      addon = {'name': section, 'verify': config.has_option(section, 'verify') and config.getboolean(section, 'verify')}
      if config.has_option(section, 'md5'):
        addon['md5'] = parse_rule(str(config.get(section, 'md5')))
      addon['main'] = parse_rule(str(config.get(section, 'main')))
      addon['files'] = []
      if config.has_option(section, 'files'):
        files_list = list(map(lambda x: x.strip(), str(config.get(section, 'files')).split(',')))
        for file in files_list:
          addon['files'].append(parse_rule(file))
      addons.append(addon)
  except:
    exc = sys.exc_info()
    log.log_ts('{}: {}'.format(exc[0], exc[1]))
  return addons

def locate_ca_bundle(dir):
  ca_bundle_path = '{}/cacert.pem'.format(dir)
  if os.path.isfile(ca_bundle_path): return ca_bundle_path
  ca_bundle_path = '{}/.gw2-addon-updater/cacert.pem'.format(dir)  # TODO: fix
  if os.path.isfile(ca_bundle_path): return ca_bundle_path
  return None

def get_node(node, verify, check, prefix, log):
  path = '{}/{}'.format(prefix, node['dest'])
  r = None
  if check:
    try:
      r = requests.get(node['src'], verify = verify)
      if os.path.isfile(path):
        with open(path, 'rb') as file:
          if r.content == file.read():
            return True
    except:
      exc = sys.exc_info()
      log.log_ts('{}: {}'.format(exc[0], exc[1]))
  try:
    if r is None: r = requests.get(node['src'], verify = verify)
    with open(path, 'wb') as file:
      file.write(r.content)
  except:
    exc = sys.exc_info()
    log.log_ts('{}: {}'.format(exc[0], exc[1]))
    return False
  return not check

def check_md5(addon, verify, env, log):
  log.log_ts('{}: checking MD5...'.format(addon['name']), info = True)
  path = '{}/{}'.format(env['game_dir'], addon['md5']['dest'])
  local_md5 = hashlib.md5()
  try:
    with open(path, "rb") as file:
      for chunk in iter(lambda: file.read(4096), b""):
          local_md5.update(chunk)
  except:
    exc = sys.exc_info()
    log.log_ts('{}: {}'.format(exc[0], exc[1]))
    return False
  try:
    return requests.get(addon['md5']['src'], verify = verify).content.decode().startswith(local_md5.hexdigest())
  except:
    exc = sys.exc_info()
    log.log_ts('{}: {}'.format(exc[0], exc[1]))
  return False

  return get_node(addon['md5'], verify, True, env['game_dir'], log)

def update_addon(addon, verify, env, log):
  log.log_ts('{} update started...'.format(addon['name']), info = True)
  if not get_node(addon['main'], verify, False, env['game_dir'], log):
    return False
  for file in addon['files']:
    if not get_node(file, verify, False, env['game_dir'], log):
      return False
  log.log_ts('{} updated successfully'.format(addon['name']), info = True)
  return True

def update_addons(env, addons, log, force, update_context):
  ca_bundle_path = locate_ca_bundle(env['script_dir'])
  for addon in addons:
    verify = addon['verify']
    if verify:
      if ca_bundle_path is None:
        log.log_ts('Error: cannot update {}, no CA bundle for SSL verification'.format(addon['name']))
        update_context['launch'] = False
        update_context['error'] = True
        continue
      os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle_path
    if 'md5' in addon and not force:
      if check_md5(addon, verify, env, log):
        log.log_ts('{} is up-to-date'.format(addon['name']), info = True)
        continue
    if not update_addon(addon, verify, env, log):
      update_context['launch'] = False
      update_context['error'] = True

def launch(game_dir, args):
  binary = '{}\\{}'.format(game_dir, 'Gw2-64.exe')
  argv = [binary]
  argv.extend(shlex.split(args))
  os.spawnv(os.P_DETACH, binary, argv)

class commands:
  EXIT          = 40001
  SHOW_LOG      = 40002
  UPDATE        = 40003
  FORCE_UPDATE  = 40004
  UPDATE_LAUNCH = 40005
  UPDATE_CA     = 40006
  LAUNCH        = 40007
  UPDATE_LOG    = 40008
