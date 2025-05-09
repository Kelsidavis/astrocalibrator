import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import webbrowser
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
import json

# Settings management: cross-platform safe location
def get_app_data_dir():
    # Windows: use APPDATA
    if os.name == 'nt' and os.getenv('APPDATA'):
        return os.path.join(os.getenv('APPDATA'), 'Astrocalibrator')
    # macOS: use ~/Library/Application Support
    elif sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Astrocalibrator')
    # Linux/Unix: use XDG_CONFIG_HOME or ~/.config
    else:
        config_home = os.getenv('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config')
        return os.path.join(config_home, 'Astrocalibrator')

# Ensure we have sys module imported
import sys

# Create settings directory and file path
SETTINGS_DIR = get_app_data_dir()
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
os.makedirs(SETTINGS_DIR, exist_ok=True)

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️ Failed to save settings: {e}")


global_icon_photo = None
toggle_log_frame = None
toggle_log_button = None

# Tooltip helper
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule_showtip)
        self.widget.bind("<Leave>", self.hidetip) 

    def schedule_showtip(self, event=None):
        self.id = self.widget.after(500, self.showtip)  # Delay tooltip popup

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def toggle_log():
    if log_embedded:
        pop_log_out_to_window()
    else:
        dock_log()

def select_output_folder():
    path = filedialog.askdirectory(title="Select Output Folder")
    if path:
        output_folder_var.set(path)
        log_message(f"📂 Output folder set to: {path}")

def dock_log():
    global external_log_window

    if external_log_window:
        try:
            external_log_window.destroy()
        except:
            pass
        external_log_window = None

    embed_log_into_main_window()


def scale_fonts(event=None):
    width = root.winfo_width()
    height = root.winfo_height()

    # Adjust scaling factor based on height
    if height >= 1000:
        size_factor = 1.2
    elif height >= 720:
        size_factor = 1.0
    else:
        size_factor = 0.9

    session_title_label.config(font=("Arial", int(16 * size_factor), "bold"))
    description_label.config(font=("Arial", int(9 * size_factor)))
    distance_label.config(font=("Arial", int(9 * size_factor)))
    progress_label.config(font=("Arial", int(9 * size_factor)))
    reset_btn.config(font=("Arial", int(10 * size_factor)))
    light_btn.config(font=("Arial", int(10 * size_factor)))
    dark_btn.config(font=("Arial", int(10 * size_factor)))
    flat_btn.config(font=("Arial", int(10 * size_factor)))
    darkflat_btn.config(font=("Arial", int(10 * size_factor)))
    bias_btn.config(font=("Arial", int(10 * size_factor)))
    master_dark_btn.config(font=("Arial", int(10 * size_factor)))
    master_flat_btn.config(font=("Arial", int(10 * size_factor)))
    master_bias_btn.config(font=("Arial", int(10 * size_factor)))

def log_message(msg):
    global saved_log_content
    print(msg)
    if log_textbox:
        log_textbox.after(0, lambda: (
            log_textbox.insert('end', msg + '\n'),
            log_textbox.see('end'),
            update_saved_log()
        ))

def update_saved_log():
    global saved_log_content
    if log_textbox:
        try:
            saved_log_content = log_textbox.get('1.0', 'end-1c')
        except:
            pass

root = tk.Tk()

# Set window title and icon (already in your code)
root.title("Astrocalibrator")

output_folder_var = tk.StringVar()

# Detect DPI scaling
dpi_scale = root.winfo_fpixels('1i') / 96  # 96 dpi = 100% scaling

def is_small_screen():
    return screen_height <= 850 or dpi_scale > 1.15

# Set custom icon from local file
try:
    icon_image = Image.open("icon.png").resize((32, 32))
    icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(False, icon_photo)
    global_icon_photo = icon_photo 
except Exception as e:
    print(f"Could not load window icon: {e}")
    global_icon_photo = None


def show_about():
    def start_move(event):
        about_window.x = event.x
        about_window.y = event.y

    def do_move(event):
        x = about_window.winfo_pointerx() - about_window.x
        y = about_window.winfo_pointery() - about_window.y
        about_window.geometry(f"+{x}+{y}")

    about_window = tk.Toplevel(root)
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    about_window.geometry(f"360x240+{root_x}+{root_y}")
    about_window.bind('<Button-1>', start_move)
    about_window.bind('<B1-Motion>', do_move)
    about_window.title("About Astrocalibrator")
    about_window.resizable(False, False)

    try:
        image = Image.open("icon.png").resize((100, 100))
        photo = ImageTk.PhotoImage(image)
        img_label = tk.Label(about_window, image=photo)
        img_label.image = photo
        img_label.pack(pady=5)
    except Exception as e:
        tk.Label(about_window, text="[Logo could not be loaded]").pack()

    tk.Label(about_window, text="Astrocalibrator", font=("Arial", 14, "bold")).pack()
    tk.Label(about_window, text="By Kelsi Davis").pack()
    tk.Label(about_window, text="https://geekastro.dev", fg="blue", cursor="hand2").pack()

    def open_site(e):
        webbrowser.open("https://geekastro.dev")

    about_window.bind_all("<Button-1>", open_site)

root.title("Astrocalibrator")

# Title Frame with Astrocalibrator Icon and Dynamic Session Title
title_frame = tk.Frame(root)
title_frame.pack(pady=(10, 5))

if os.path.exists("icon.png"):
    title_img = Image.open("icon.png").resize((32, 32))
    title_photo = ImageTk.PhotoImage(title_img)
    icon_label = tk.Label(title_frame, image=title_photo)
    icon_label.image = title_photo  # Keep a reference!
    icon_label.pack(side='left', padx=5)

session_title_var = tk.StringVar(value="Welcome to Astrocalibrator!")
session_title_label = tk.Label(title_frame, textvariable=session_title_var, font=("Arial", 16, "bold"))
ToolTip(session_title_label, "Displays the current imaging session name or object being calibrated.")
session_title_label.pack(side='left', padx=5)

# Container for session object description and distance
session_info_frame = tk.Frame(root)
session_info_frame.pack(pady=5)

object_description_var = tk.StringVar(value="")
object_distance_var = tk.StringVar(value="")

description_label = tk.Label(session_info_frame, textvariable=object_description_var, font=("Arial", 9))
description_label.pack()

distance_label = tk.Label(session_info_frame, textvariable=object_distance_var, font=("Arial", 9))
distance_label.pack()

max_threads_var = tk.IntVar(value=os.cpu_count())
progress_var = tk.DoubleVar()

# Create progress bar linked to progress_var
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, mode="determinate", style="TProgressbar")
progress_bar.pack(fill='x', padx=10, pady=(2, 4))
progress_label_var = tk.StringVar(value="Idle")
progress_label = tk.Label(root, textvariable=progress_label_var, font=("Arial", 9), anchor='center')
progress_label.pack(pady=(0, 4))

master_dark_path = tk.StringVar()
master_flat_path = tk.StringVar()
master_bias_path = tk.StringVar()

astap_path_var = tk.StringVar()

# Load user settings
user_settings = load_settings()

    # Enforce default ASTAP path if missing
if 'astap_path' not in user_settings:
    user_settings['astap_path'] = "C:/Program Files/ASTAP"
    save_settings(user_settings)

if 'output_folder' not in user_settings:
    user_settings['output_folder'] = ""
    save_settings(user_settings)

# Preload saved ASTAP path if available
if 'astap_path' in user_settings:
    astap_path_var.set(user_settings['astap_path'])


master_dark_enabled = tk.BooleanVar()
master_flat_enabled = tk.BooleanVar()
master_bias_enabled = tk.BooleanVar()

# Frame selector section
light_files, dark_files, flat_files, dark_flat_files, bias_files = [], [], [], [], []

from astropy.io import fits

def select_file(path_var):
    filename = filedialog.askopenfilename(
        title="Select File",
        filetypes=[("FITS files", "*.fits"), ("All files", "*.*")]
    )
    if filename:
        path_var.set(filename)

import threading

def select_files(file_list, label, expected_type=None):
    try:
        title = f"Select {expected_type.title()}" if expected_type else "Select Files"
        files = filedialog.askopenfilenames(title=title, filetypes=[("FITS files", "*.fits")])
        if files:
            root.config(cursor="watch")

            def process_files():
                validated_files = list(files)
                file_list.clear()
                file_list.extend(validated_files)

                def update_ui():
                    label.config(text=f"{len(validated_files)} {expected_type.title()} Selected" if expected_type else f"{len(validated_files)} files selected")

                    if expected_type == "DARK":
                        master_dark_enabled.set(False)
                    elif expected_type == "FLAT":
                        master_flat_enabled.set(False)
                    elif expected_type == "BIAS":
                        master_bias_enabled.set(False)
                    elif expected_type == "DARKFLAT":
                        pass

                    if validated_files:
                        messagebox.showinfo(
                            "Selection Complete",
                            f"{len(validated_files)} {expected_type.title()} selected successfully."
                        )

                    root.config(cursor="")  # ✅ Restore normal cursor

                    if expected_type == "LIGHT":
                        root.after(1000, try_run_plate_solving)

                root.after(0, update_ui)

            root.after(10, process_files)

    except Exception as e:
        root.config(cursor="")
        raise e

    
def update_ui():
    light_label.config(text=f"{len(light_files)} lights selected")
    dark_label.config(text=f"{len(dark_files)} darks selected")
    flat_label.config(text=f"{len(flat_files)} flats selected")
    bias_label.config(text=f"{len(bias_files)} bias selected")

frame_select_container = tk.LabelFrame(root, text="Select calibration input frames", font=("Arial", 9))
frame_select_container.pack(pady=10, padx=10, fill='x')
frame_select_info = tk.Label(frame_select_container, text="Choose the raw light, dark, flat, and dark flat frames to be used for this calibration session.", font=("Arial", 8), wraplength=500, justify='center')
frame_select_info.pack(pady=(0, 5))
file_frame = tk.Frame(frame_select_container)
file_frame.pack()

light_label = tk.Label(file_frame, text="No files")
dark_label = tk.Label(file_frame, text="No files")
flat_label = tk.Label(file_frame, text="No files")
darkflat_label = tk.Label(file_frame, text="No files")

light_btn = tk.Button(file_frame, text="Select Lights", command=lambda: select_files(light_files, light_label, expected_type="LIGHT"))
ToolTip(light_btn, "Select your primary astrophotography images (LIGHT frames).")
dark_btn = tk.Button(file_frame, text="Select Darks", command=lambda: select_files(dark_files, dark_label, expected_type="DARK"))
ToolTip(dark_btn, "Select DARK frames: Same exposure as lights but with no light entering the camera.")
flat_btn = tk.Button(file_frame, text="Select Flats", command=lambda: select_files(flat_files, flat_label, expected_type="FLAT"))
ToolTip(flat_btn, "Select FLAT frames: Images of uniform light to correct optical system artifacts.")
darkflat_btn = tk.Button(file_frame, text="Select Dark Flats", command=lambda: select_files(dark_flat_files, darkflat_label, expected_type="DARKFLAT"))
ToolTip(darkflat_btn, "Select DARK FLAT frames: Dark exposures matching flat frame settings.")

bias_label = tk.Label(file_frame, text="No files")

bias_btn = tk.Button(file_frame, text="Select Bias Frames", command=lambda: select_files(bias_files, bias_label, expected_type="BIAS"))
ToolTip(bias_btn, "Select BIAS frames: Fastest exposures to calibrate camera electronics.")

for btn, label in zip([light_btn, dark_btn, flat_btn, darkflat_btn, bias_btn], [light_label, dark_label, flat_label, darkflat_label, bias_label]):
    row = [light_btn, dark_btn, flat_btn, darkflat_btn, bias_btn].index(btn)
    btn.grid(row=row, column=0, padx=5, pady=2, sticky='w')
    label.grid(row=row, column=1, sticky='w')

# Master calibration section
master_frame_container = tk.LabelFrame(root, text="Or use existing calibration masters", font=("Arial", 9))
master_frame_container.pack(pady=10, padx=10, fill='x')
master_frame_info = tk.Label(master_frame_container, text="Enable one or more of the options below to apply pre-generated master calibration files.", font=("Arial", 8), wraplength=500, justify='center')
master_frame_info.pack(pady=(0, 5))
master_frame = tk.Frame(master_frame_container)
master_frame.pack()

master_dark_btn = tk.Button(master_frame, text="Select Master Dark", command=lambda: browse_file(master_dark_path))
ToolTip(master_dark_btn, "Choose a pre-generated Master Dark frame to subtract thermal noise from your lights.")
master_dark_label = tk.Label(master_frame, text="No master selected", wraplength=300)
master_flat_btn = tk.Button(master_frame, text="Select Master Flat", command=lambda: browse_file(master_flat_path))
ToolTip(master_flat_btn, "Choose a Master Flat frame to correct uneven illumination (vignetting/dust).")
master_flat_label = tk.Label(master_frame, text="No master selected", wraplength=300)
master_bias_btn = tk.Button(master_frame, text="Select Master Bias", command=lambda: browse_file(master_bias_path))
ToolTip(master_bias_btn, "Choose a Master Bias frame to correct for electronic readout noise.")
master_bias_label = tk.Label(master_frame, text="No master selected", wraplength=300)

master_dark_btn.grid(row=0, column=0, sticky='w', padx=5, pady=2)
master_dark_label.grid(row=0, column=1, sticky='w')

master_flat_btn.grid(row=1, column=0, sticky='w', padx=5, pady=2)
master_flat_label.grid(row=1, column=1, sticky='w')

master_bias_btn.grid(row=2, column=0, sticky='w', padx=5, pady=2)
master_bias_label.grid(row=2, column=1, sticky='w')

def toggle_input_state():
    light_btn.config(state=tk.NORMAL)

    if not master_dark_path.get():
        master_dark_enabled.set(False)
    if not master_flat_path.get():
        master_flat_enabled.set(False)
    if not master_bias_path.get():
        master_bias_enabled.set(False)

    if master_dark_enabled.get() and master_dark_path.get():
        dark_btn.config(state=tk.DISABLED)
        dark_label.config(text="Master Selected")
    else:
        dark_btn.config(state=tk.NORMAL)
        dark_label.config(text="No files")

    if master_flat_enabled.get() and master_flat_path.get():
        flat_btn.config(state=tk.DISABLED)
        flat_label.config(text="Master Selected")
    else:
        flat_btn.config(state=tk.NORMAL)
        flat_label.config(text="No files")

    darkflat_btn.config(state=tk.NORMAL)

    if master_bias_enabled.get() and master_bias_path.get():
        bias_btn.config(state=tk.DISABLED)
        bias_label.config(text="Master Selected")
    else:
        bias_btn.config(state=tk.NORMAL)
        bias_label.config(text="No files")

def full_reset():
    # Reset session fields
    session_title_var.set("Welcome to Astrocalibrator!")
    object_description_var.set("")
    object_distance_var.set("")

    # Reset progress bar
    progress_var.set(0)
    progress_label_var.set("Idle")
    progress_bar.stop()
    progress_bar.config(mode="determinate")

    # Clear frame file lists
    light_files.clear()
    dark_files.clear()
    flat_files.clear()
    dark_flat_files.clear()
    bias_files.clear()

    # Clear labels next to buttons
    light_label.config(text="No files")
    dark_label.config(text="No files")
    flat_label.config(text="No files")
    darkflat_label.config(text="No files")
    bias_label.config(text="No files")

    # Reset master frames
    master_dark_path.set("")
    master_flat_path.set("")
    master_bias_path.set("")
    master_dark_label.config(text="No master selected")
    master_flat_label.config(text="No master selected")
    master_bias_label.config(text="No master selected")
    master_dark_enabled.set(False)
    master_flat_enabled.set(False)
    master_bias_enabled.set(False)

    # Clear log window
    if log_textbox:
        log_textbox.delete('1.0', tk.END)

    # Output folder remains unchanged!

    root.after(10, toggle_input_state)

    log_message("🔄 Reset complete. Output folder unchanged.")

reset_btn = tk.Button(root, text="Reset Options", command=full_reset)
ToolTip(reset_btn, "Clear all selected frames and reset calibration settings to default.")
reset_btn.pack(pady=5)

# Globals
log_embedded = True
external_log_window = None
log_frame = None
log_textbox = None
scrollbar = None
saved_log_content = ""

def get_current_log_content():
    global saved_log_content
    if log_textbox:
        try:
            saved_log_content = log_textbox.get('1.0', 'end-1c')
        except:
            pass
    return saved_log_content

def shrink_root_for_log_popout():
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    root.geometry(f"{width}x{height-160}")

def expand_root_for_log_dock():
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    root.geometry(f"{width}x{height+160}")

def embed_log_into_main_window():
    global log_embedded, external_log_window, log_frame, log_textbox, scrollbar, saved_log_content
    global toggle_log_frame, toggle_log_button   # ✅ ADD THIS

    get_current_log_content()

    # 🔥 Destroy old toggle_log_frame if it exists
    if toggle_log_frame:
        try:
            toggle_log_frame.destroy()
        except:
            pass
        toggle_log_frame = None

    if log_frame:
        try:
            log_frame.destroy()
        except:
            pass
        log_frame = None

    if external_log_window:
        try:
            external_log_window.destroy()
        except:
            pass
        external_log_window = None

    # 🛠 Create new toggle_log_frame and button
    toggle_log_frame = tk.Frame(root)
    toggle_log_button = tk.Button(toggle_log_frame, text="Pop Out Log", command=toggle_log)
    toggle_log_button.pack(side='left', padx=(10,0))
    toggle_log_frame.pack(fill='x', pady=(5, 0), padx=10)

    # 🛠 Create new log frame and textbox
    log_frame = tk.Frame(root)
    log_textbox = tk.Text(log_frame, wrap='word', height=7)
    scrollbar = ttk.Scrollbar(log_frame, command=log_textbox.yview)
    log_textbox.config(yscrollcommand=scrollbar.set)

    log_textbox.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    log_frame.pack(side='bottom', fill='both', expand=True, padx=10, pady=(0, 5))

    # Restore saved log content
    log_textbox.insert('1.0', saved_log_content)
    log_textbox.mark_set("insert", "end")
    log_textbox.focus()
    log_textbox.see('end')

    log_embedded = True
    toggle_log_button.config(text="Pop Out Log")

def pop_log_out_to_window():
    global log_embedded, external_log_window, log_frame, log_textbox, scrollbar, toggle_log_frame, toggle_log_button

    # Capture log text BEFORE destroying anything
    current_log = ""
    if log_textbox:
        try:
            current_log = log_textbox.get('1.0', 'end-1c')
        except:
            pass

    # Destroy old frames
    if log_frame:
        try:
            log_frame.destroy()
        except:
            pass
        log_frame = None

    if toggle_log_frame:
        try:
            toggle_log_frame.destroy()
        except:
            pass
        toggle_log_frame = None
        toggle_log_button = None

    root.update_idletasks()
    root.update()

    # Create external log window
    external_log_window = tk.Toplevel(root)
    external_log_window.title("Astrocalibrator Log")
    if global_icon_photo:
        external_log_window.iconphoto(False, global_icon_photo)
    external_log_window.geometry("600x300")
    external_log_window.protocol("WM_DELETE_WINDOW", dock_log)

    # 🛠 New Position: next to main window
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    external_x = root_x + root_width + 10  # 10 pixels right
    external_y = root_y
    external_log_window.geometry(f"+{external_x}+{external_y}")

    log_frame = tk.Frame(external_log_window)
    log_textbox = tk.Text(log_frame, wrap='word', height=7)
    scrollbar = ttk.Scrollbar(log_frame, command=log_textbox.yview)
    log_textbox.config(yscrollcommand=scrollbar.set)

    log_textbox.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))

    if current_log:
        log_textbox.insert('1.0', current_log)
    log_textbox.see('end')

    log_embedded = False
    
    # Bring both windows to the foreground
    root.lift()  # Bring main window to the foreground
    root.focus_force()  # Force focus on main window
    
    # Bring log window to the foreground after a short delay
    # This ensures both windows are visible to the user
    root.after(100, lambda: external_log_window.lift())


def browse_file(var):
    path = filedialog.askopenfilename(title="Select Master Calibration Frame", filetypes=[("FITS files", "*.fits")])
    if path:
        var.set(path)
        filename = os.path.basename(path)
        if var == master_dark_path:
            master_dark_label.config(text=filename)
            master_dark_enabled.set(True)
            dark_label.config(text="Master Selected")
        elif var == master_flat_path:
            master_flat_label.config(text=filename)
            master_flat_enabled.set(True)
            flat_label.config(text="Master Selected")
        elif var == master_bias_path:
            master_bias_label.config(text=filename)
            master_bias_enabled.set(True)
            bias_label.config(text="Master Selected")
        toggle_input_state()
        root.update_idletasks()  # Force immediate redraw here!

def set_astap_location():
    existing_path = astap_path_var.get()
    if existing_path and os.path.isdir(existing_path):
        initial_folder = existing_path
    else:
        initial_folder = "C:/Program Files/ASTAP"

    path = filedialog.askopenfilename(
        title="Select ASTAP Executable",
        initialdir=initial_folder,
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    if path:
        astap_path_var.set(path)
        user_settings['astap_path'] = os.path.dirname(path)  # Save FOLDER not FILE
        save_settings(user_settings)
        log_message(f"🔧 ASTAP location set: {path}")
        auto_close_message("Settings Saved", "✅ ASTAP location saved successfully!", timeout=2000)

def auto_close_message(title, message, timeout=2000):
    top = tk.Toplevel(root)
    top.title(title)
    top.geometry("300x100")
    top.resizable(False, False)
    label = tk.Label(top, text=message, font=("Arial", 10))
    label.pack(expand=True, pady=20)
    top.after(timeout, top.destroy)
    # Center the popup
    top.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (top.winfo_width() // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (top.winfo_height() // 2)
    top.geometry(f"+{x}+{y}")

# Now call UI initialization after everything is defined

# Create top menu bar
menubar = tk.Menu(root)

# Settings Menu
settingsmenu = tk.Menu(menubar, tearoff=0)
settingsmenu.add_command(label="Set ASTAP Location", command=set_astap_location)
menubar.add_cascade(label="Settings", menu=settingsmenu)


# Help Menu
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=show_about)
menubar.add_cascade(label="Help", menu=helpmenu)

# Attach menubar to root window
root.config(menu=menubar)

def handle_root_configure(event=None):
    scale_fonts(event)

def finalize_window_size():
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    root.geometry(f"{width}x{height}+{root.winfo_x()}+{root.winfo_y()}")
    root.minsize(width, height)
    root.maxsize(width, height)

root.after(200, finalize_window_size)

def try_run_plate_solving():
    from main import run_plate_solving
    if output_folder_var.get() and light_files:
        log_message("🚀 Lights selected. Preparing plate solving...")
        run_plate_solving()
    else:
        log_message("⚠️ Output folder not selected. Cannot start solving yet.")

def prompt_for_output_folder():
    if not output_folder_var.get():
        selected_folder = filedialog.askdirectory(title="Select Output Folder for Calibrated Images")
        if selected_folder:
            output_folder_var.set(selected_folder)
            log_message(f"📂 Output folder set to: {selected_folder}")
        else:
            messagebox.showwarning("No Folder Selected", "⚠️ No output folder selected. Calibration cannot proceed without a destination folder.")

# Set up initial log docking based on screen size
root.after(100, pop_log_out_to_window)

# Now we resize and center properly
window_width = 470
window_height = 720
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.minsize(window_width, window_height)
root.maxsize(window_width, window_height)

#root.after(300, prompt_for_output_folder) <--- this needs fixed to support the button states first


# --- Export GUI components to main.py ---
__all__ = [
    "root", "log_message", "log_textbox", "output_folder_var", "progress_var", "progress_label_var", "progress_label",
    "session_title_var", "master_dark_path", "master_flat_path", "master_bias_path",
    "master_dark_enabled", "master_flat_enabled", "master_bias_enabled",
    "ToolTip",
    "light_files", "dark_files", "flat_files", "bias_files",
    "file_frame", "light_label", "dark_label", "flat_label",
    "light_btn", "dark_btn", "flat_btn", "bias_btn", "darkflat_btn",
    "reset_btn",
    "master_dark_btn", "master_flat_btn", "master_bias_btn",
    "progress_bar",
    "object_description_var", "object_distance_var"
]

