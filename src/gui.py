# (C) unresolved-external@singu-lair.com released under the MIT license (see LICENSE)

import os
import struct
import win32api
import win32event
import win32con
import win32gui
import winerror

class shell_icon:
  hWnd    = None
  message = None
  hIcon   = None
  tip     = ""

  def __init__(self, hWnd, message):
    self.hWnd     = hWnd
    self.message  = message

  def load(self, icon_value):
    if type(icon_value) is icon:
      self.hIcon = icon_value.hIcon
    elif type(icon_value) is int:
      self.hIcon = icon_value
    else:
      def try_load(filename):
        try: i = win32gui.LoadImage(None, filename, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE | win32con.LR_SHARED)
        except: i = None
        return i
      self.hIcon = try_load(filename)
      if self.hIcon is None: self.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

  def show(self):
    flags       = win32gui.NIF_MESSAGE | win32gui.NIF_ICON | win32gui.NIF_TIP
    nid         = (self.hWnd, win32con.IDI_APPLICATION, flags, self.message, self.hIcon, self.tip)
    win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

  def hide(self):
    nid         = (self.hWnd, win32con.IDI_APPLICATION)
    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)

  def set_tip(self, new_tip):
    self.tip = new_tip
    flags       = win32gui.NIF_TIP
    nid         = (self.hWnd, win32con.IDI_APPLICATION, flags, 0, 0, self.tip)
    win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

  def notify(self, title, text):
    flags       = win32gui.NIF_INFO
    nid         = (self.hWnd, win32con.IDI_APPLICATION, flags, 0, 0, "", text, 0, title)
    win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

class icon:
  hIcon = None

  def __init__(self, filename):
    def try_load(filename):
      try: icon = win32gui.LoadImage(None, filename, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE | win32con.LR_SHARED)
      except: icon = None
      return icon
    self.hIcon = try_load(filename)
    if self.hIcon is None: self.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

class window_class:
  name        = None
  hInstance   = None
  class_atom  = None

  def __init__(self, name, message_map, hInstance = None, icon = None):
    self.name = name
    self.hInstance = hInstance if hInstance else win32api.GetModuleHandle(None)
    wc                = win32gui.WNDCLASS()
    wc.style          = win32con.CS_HREDRAW | win32con.CS_VREDRAW
    wc.lpfnWndProc    = message_map
    wc.cbWndExtra     = 0
    wc.hInstance      = self.hInstance
    wc.hIcon          = icon if icon is not None else win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
    wc.hCursor        = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wc.hbrBackground  = win32con.COLOR_WINDOW + 1
    wc.lpszClassName  = self.name
    # C code: wc.cbWndExtra = DLGWINDOWEXTRA + sizeof(HBRUSH) + (sizeof(COLORREF));
    wc.cbWndExtra     = win32con.DLGWINDOWEXTRA + struct.calcsize("Pi")
    self.class_atom   = win32gui.RegisterClass(wc)

class window:
  hWnd      = None

  def __init__(self, name : str, class_name : str, hInstance = None, style = None, ex_style = None,
               x : int = win32con.CW_USEDEFAULT, y : int = win32con.CW_USEDEFAULT, width : int = win32con.CW_USEDEFAULT, height : int = win32con.CW_USEDEFAULT, parent = None):
    self.hInstance = hInstance if hInstance else win32api.GetModuleHandle(None)
    style     = style if style is not None else win32con.WS_OVERLAPPEDWINDOW
    ex_style  = ex_style if ex_style is not None else win32con.WS_EX_CLIENTEDGE
    if type(parent) is window:
      parent = parent.hWnd
    elif parent is None:
      parent = 0
    self.hWnd = win32gui.CreateWindowEx(ex_style, class_name, name, style, x, y, width, height, parent, 0, self.hInstance, None)

  def show(self):
    win32gui.ShowWindow(self.hWnd, win32con.SW_SHOW)

  def hide(self):
    win32gui.ShowWindow(self.hWnd, win32con.SW_HIDE)
