# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import win32api
import win32con
import win32event
import win32gui
import winreg
import winerror
import os
import sys

from multiprocessing import Queue  # hack

import common
import gui
import tray_log
import updater_thread

class tray_app:
  UUID                    = "{61053809-1E96-4C84-8D4B-DD1766180FF2}"
  WM_USER_SHELLICON       = win32con.WM_USER + 1

  app_icon            = None

  icon_class          = None
  icon_window         = None
  icon_icon           = None

  log_class           = None
  log_window          = None

  log                 = None
  updater             = None

  env                 = {}

  def __init__(self):
    self.log      = tray_log.log()
    self.updater  = updater_thread.updater_thread()

  def run(self):
    self.log.start()
    self.env = common.load_env(self.log)
    if self.env['game_dir'] is None:
      win32gui.MessageBox(0, 'Cannot locate Guild Wars 2\r\nSet path to Guild Wars 2 in your \'gw2-addon-updater.ini\' file', 'gw2-addon-updater', win32con.MB_OK | win32con.MB_ICONERROR)
      self.log.stop()
      return
    win32gui.InitCommonControls()
      # force single instance
    self.mutex = win32event.CreateMutex(None, False, "single_mutex_" + self.UUID)
    lasterror = win32api.GetLastError()
    if (lasterror == winerror.ERROR_ALREADY_EXISTS) or (lasterror == winerror.ERROR_ACCESS_DENIED):
      os._exit(1)
    self.app_icon = gui.icon('gw2-addon-updater.ico')
    self.icon_class   = gui.window_class("Guild Wars 2 Addon Updater", icon = self.app_icon.hIcon, message_map = {
      win32con.WM_DESTROY:    self.icon_on_destroy,
      win32con.WM_CLOSE:      self.icon_on_close,
      win32con.WM_COMMAND:    lambda hWnd, message, wp, lp, self=self: self.icon_process_command(win32api.LOWORD(wp)),
      self.WM_USER_SHELLICON: lambda hWnd, message, wp, lp, self=self: self.icon_process_shell_icon(win32api.LOWORD(lp)),
    })
    self.icon_window  = gui.window("Guild Wars 2 Addon Updater", self.icon_class.name)
    self.icon_icon    = gui.shell_icon(self.icon_window.hWnd, self.WM_USER_SHELLICON)
    self.log.bind_hwnd(self.icon_window.hWnd)
    desktop_rect = win32gui.GetClientRect(win32gui.GetDesktopWindow())
    self.log_class    = gui.window_class("Guild Wars 2 Addon Updater Log", icon = 0, message_map = {
      win32con.WM_DESTROY:    self.log_on_destroy,
      win32con.WM_CLOSE:      self.log_on_close,
      win32con.WM_SIZE:       self.log_on_size,
      win32con.WM_ACTIVATE:   self.log_on_activate,
    })
    log_style     = win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_THICKFRAME
    log_ex_style  = win32con.WS_EX_TOOLWINDOW
    log_width     = 600
    log_height    = 800
    log_margin    = 60
    log_x         = desktop_rect[2] - log_width - log_margin
    log_y         = desktop_rect[3] - log_height - log_margin
    self.log_window       = gui.window("Log", self.log_class.name, style = log_style, ex_style = log_ex_style, x = log_x, y = log_y, width = log_width, height = log_height)
    edit_style    = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_VSCROLL | win32con.ES_LEFT | win32con.ES_MULTILINE | win32con.ES_AUTOVSCROLL
    self.log_window.edit  = gui.window("", "EDIT", style = edit_style, x = 0, y = 0, parent = self.log_window)
    self.icon_icon.load(self.app_icon)
    self.icon_icon.show()
    self.updater.start(self.env, self.icon_window.hWnd, self.log)
    win32gui.PumpMessages()
    self.updater.stop()
    self.log.stop()

  def icon_on_destroy(self, hWnd, message, wp, lp):
    self.icon_icon.hide()
    win32gui.PostQuitMessage(0)
    return True

  def icon_on_close(self, hWnd, message, wp, lp):
    win32gui.DestroyWindow(hWnd)
    return True

  def icon_process_command(self, value):
    if value == common.commands.EXIT:
      win32gui.DestroyWindow(self.icon_window.hWnd)
    elif value == common.commands.SHOW_LOG:
      self.log_window.show()
      win32gui.SetFocus(self.log_window.hWnd)
      log = self.log.extract()
      win32gui.SetWindowText(self.log_window.edit.hWnd, '\r\n'.join(log))
    elif value == common.commands.UPDATE_LAUNCH:
      if self.env['game_dir'] is None:
        self.icon_icon.notify('gw2-addon-updater', 'Cannot locate Guild Wars 2')
      else:
        self.updater.update_launch()
    elif value == common.commands.UPDATE:
      if self.env['game_dir'] is None:
        self.icon_icon.notify('gw2-addon-updater', 'Cannot locate Guild Wars 2')
      else:
        self.updater.update()
    elif value == common.commands.FORCE_UPDATE:
      if self.env['game_dir'] is None:
        self.icon_icon.notify('gw2-addon-updater', 'Cannot locate Guild Wars 2')
      else:
        self.updater.force_update()
    elif value == common.commands.UPDATE_CA:
      self.updater.force_update_ca_bundle()
    elif value == common.commands.LAUNCH:
      common.launch(self.env['game_dir'], self.env['game_args'])
    elif value == common.commands.UPDATE_LOG:
      log = self.log.extract()
      win32gui.SetWindowText(self.log_window.edit.hWnd, '\r\n'.join(log))
    return True

  def icon_process_shell_icon(self, value):
    if value == win32con.WM_RBUTTONDOWN:
      menu = win32gui.CreatePopupMenu()
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.UPDATE_LAUNCH, 'Update and launch')
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.UPDATE, 'Update only')
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.FORCE_UPDATE, 'Force update')
      win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, '')
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.UPDATE_CA, 'Update CA Bundle')
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.SHOW_LOG, 'Show Log')
      win32gui.AppendMenu(menu, win32con.MF_STRING, common.commands.EXIT, 'Exit')
      win32gui.SetMenuDefaultItem(menu, common.commands.UPDATE_LAUNCH, False)
      win32gui.SetForegroundWindow(self.icon_window.hWnd)
      pos = win32gui.GetCursorPos()
      win32gui.TrackPopupMenu(menu, win32gui.TPM_LEFTALIGN | win32gui.TPM_LEFTBUTTON | win32gui.TPM_BOTTOMALIGN, pos[0], pos[1], 0, self.icon_window.hWnd, None)
      win32api.SendMessage(self.icon_window.hWnd, win32con.WM_NULL, 0, 0)
    return True

  def log_on_destroy(self, hWnd, message, wp, lp):
    return True

  def log_on_close(self, hWnd, message, wp, lp):
    self.log_window.hide()
    return True

  def log_on_size(self, hWnd, message, wp, lp):
    width = win32api.LOWORD(lp)
    height = win32api.HIWORD(lp)
    win32gui.SetWindowPos(self.log_window.edit.hWnd, 0, 0, 0, width, height, 0)
    return True;

  def log_on_activate(self, hWnd, message, wp, lp):
    if win32api.LOWORD(wp) == win32con.WA_INACTIVE:
      self.log_window.hide()
    return True

a = tray_app()
a.run()
