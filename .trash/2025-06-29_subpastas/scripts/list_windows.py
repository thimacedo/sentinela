import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

def enum_windows():
    windows = []
    def enum_windows_proc(hwnd, lParam):
        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        is_visible = user32.IsWindowVisible(hwnd) != 0
        windows.append((hwnd, pid.value, title, is_visible))
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
    return windows

for hwnd, pid, title, is_visible in enum_windows():
    if pid == 17404:
        print(f"PID: {pid}, HWND: {hwnd}, Title: '{title}', Visible: {is_visible}")
