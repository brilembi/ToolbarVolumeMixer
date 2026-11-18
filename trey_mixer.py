import tkinter as tk
from tkinter import ttk
import threading
import sys
import os
import winreg
from pycaw.pycaw import AudioUtilities
import pystray
from PIL import Image, ImageDraw

class VolumeMixer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aero Volume Mixer")
        self.geometry("350x450")
        self.attributes('-topmost', True)
        self.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        # Frutiger Aero Color Palette
        self.bg_color = '#E4F3FB'       # Glossy sky/cloud white
        self.header_color = '#B0DEF7'   # Glassy sky blue
        self.text_color = '#003366'     # Deep blue for high readability
        
        self.configure(bg=self.bg_color)
        
        # Position above the tray
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"+{screen_width - 360}+{screen_height - 520}")
        
        # UI Styling
        style = ttk.Style()
        # Attempt to use older Windows native styling if available
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        elif 'xpnative' in style.theme_names():
            style.theme_use('xpnative')
            
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.text_color, font=('Segoe UI', 10))
        
        # Custom Header Frame
        header_frame = tk.Frame(self, bg=self.header_color, bd=1, relief='ridge')
        header_frame.pack(fill='x', padx=5, pady=5)
        
        title_label = tk.Label(header_frame, text="Active Applications", 
                               bg=self.header_color, fg='#004080', font=('Segoe UI', 12, 'bold'))
        title_label.pack(side='left', padx=10, pady=10)
        
        refresh_btn = tk.Button(header_frame, text="↻ Refresh", bg='#FFFFFF', fg=self.text_color, 
                                relief='groove', font=('Segoe UI', 9),
                                command=self.refresh_audio_sessions)
        refresh_btn.pack(side='right', padx=10, ipadx=5, ipady=2)

        self.apps_container = ttk.Frame(self)
        self.apps_container.pack(fill='both', expand=True)
        
        self.refresh_audio_sessions()
        
    def refresh_audio_sessions(self):
        for widget in self.apps_container.winfo_children():
            widget.destroy()
            
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            volume = session.SimpleAudioVolume
            app_name = session.Process.name() if session.Process else "System Sounds"
            
            if app_name == "System Sounds" and not session.Process:
                continue
                
            frame = tk.Frame(self.apps_container, bg=self.bg_color, bd=2, relief='groove')
            frame.pack(fill='x', padx=10, pady=5)
            
            label = tk.Label(frame, text=app_name, width=15, bg=self.bg_color, fg=self.text_color, anchor='w')
            label.pack(side='left', padx=5, pady=8)
            
            current_vol = volume.GetMasterVolume()
            slider = ttk.Scale(frame, from_=0, to=1, orient='horizontal', 
                               command=lambda val, vol=volume: vol.SetMasterVolume(float(val), None))
            slider.set(current_vol)
            slider.pack(side='right', fill='x', expand=True, padx=10, pady=8)

    def hide_window(self):
        self.withdraw()

# --- Auto-Startup Logic ---
def setup_autostart():
    # Only configure autostart if running as a compiled .exe
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "AeroVolumeMixer", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
        except Exception as e:
            pass # Fails silently if registry access is denied

# --- Frutiger Aero Tray Icon ---
icon_instance = None

def create_tray_image():
    # Draws a glossy blue orb with a white speaker icon (Aero Style)
    image = Image.new('RGB', (64, 64), color=(228, 243, 251))
    draw = ImageDraw.Draw(image)
    
    # Base blue circle
    draw.ellipse([4, 4, 60, 60], fill=(77, 166, 255))
    # Inner glow
    draw.ellipse([8, 8, 56, 56], fill=(102, 179, 255))
    # Top glossy highlight
    draw.ellipse([16, 6, 48, 24], fill=(200, 230, 255))
    
    # Speaker icon
    draw.polygon([(20, 28), (28, 28), (42, 16), (42, 48), (28, 36), (20, 36)], fill=(255, 255, 255))
    return image

def setup_tray(app):
    global icon_instance
    menu = pystray.Menu(
        pystray.MenuItem('Open Mixer', lambda: app.after(0, app.deiconify), default=True),
        pystray.MenuItem('Exit', exit_app)
    )
    icon_instance = pystray.Icon("AeroMixer", create_tray_image(), "Aero Mixer", menu)
    icon_instance.run()

def exit_app():
    if icon_instance:
        icon_instance.stop()
    app.quit()
    sys.exit()

if __name__ == '__main__':
    setup_autostart()
    
    app = VolumeMixer()
    app.withdraw()
    
    tray_thread = threading.Thread(target=setup_tray, args=(app,), daemon=True)
    tray_thread.start()
    
    app.mainloop()