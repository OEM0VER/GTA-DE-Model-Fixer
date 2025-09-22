import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import subprocess
import sys
import webbrowser
from PIL import Image, ImageTk
import ctypes
import ctypes.wintypes
from win32com.client import Dispatch
import gdown
import requests
import zipfile
import io
import shutil
import threading
import ctypes
from ctypes import windll

def get_script_directory():
    if getattr(sys, 'frozen', False):
        # The script is bundled into an executable
        return os.path.abspath(os.path.dirname(sys.executable))
    else:
        # The script is run directly
        return os.path.abspath(os.path.dirname(__file__))

def download_and_extract_files():
    print("[LOG] 'Files' folder not found. Downloading…")
    
    url = "https://drive.google.com/uc?id=1VFpiBVSSNVsjB0H6tFAmkJiJMtWf4oBg"
    zip_path = os.path.join(get_script_directory(), "files.zip")
    files_folder = os.path.join(get_script_directory(), "Files")
    
    # Ensure base folder exists
    os.makedirs(files_folder, exist_ok=True)

    # Download the zip
    gdown.download(url, zip_path, quiet=True)

    # Extract to temp folder
    temp_extract = os.path.join(get_script_directory(), "temp_files")
    os.makedirs(temp_extract, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_extract)

    # Move inner folder contents to Files folder
    inner_folder = os.path.join(temp_extract, "Files")  # the folder inside the zip
    if os.path.exists(inner_folder):
        for item in os.listdir(inner_folder):
            src = os.path.join(inner_folder, item)
            dst = os.path.join(files_folder, item)
            if os.path.isdir(src):
                shutil.move(src, dst)  # safe merge
            else:
                shutil.move(src, dst)

    # Clean up
    shutil.rmtree(temp_extract)
    os.remove(zip_path)
    print("[LOG] Download and extraction complete!")

def ensure_files_folder():
    files_folder = os.path.join(get_script_directory(), "Files")
    if os.path.exists(files_folder):
        print("[LOG] 'Files' folder already exists.")
        return

    download_and_extract_files()  # blocking, console download

def run_fix_model():
    # Open file dialog to select a .uasset file
    file_path = filedialog.askopenfilename(
        title="Select a UAsset file",
        filetypes=[("UAsset Files", "*.uasset")]
    )

    if not file_path:
        return  # user cancelled

    # Build path to the MeshAibRemover.exe in the Files folder
    exe_path = os.path.join(get_script_directory(), "Files", "MeshAibRemover.exe")
    if not os.path.exists(exe_path):
        messagebox.showerror("Error", f"MeshAibRemover.exe not found:\n{exe_path}")
        return

    try:
        # Run the MeshAibRemover.exe in its own console
        subprocess.run([exe_path, file_path])

        # Show success message after it finishes
        messagebox.showinfo("Success", f"File processed successfully:\n{file_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An exception occurred:\n{e}")

def create_desktop_shortcut(shortcut_name="Model Fixer"):
    """
    Create a shortcut for the application on the desktop.
    """
    try:
        script_dir = get_script_directory()
        target_path = os.path.join(script_dir, "GTA_DE_Model_Fixer.exe")  # adjust if your exe name is different

        # Get the desktop folder path
        desktop_path = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetSpecialFolderPathW(None, desktop_path, 0x00, False)

        # Shortcut path
        shortcut_path = os.path.join(desktop_path.value, f"{shortcut_name}.lnk")

        # Create the shortcut
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = script_dir
        shortcut.IconLocation = target_path
        shortcut.Save()

        messagebox.showinfo("Success", f"Desktop shortcut '{shortcut_name}' created!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create shortcut:\n{e}")

def open_dotnet_download():
    webbrowser.open("https://dotnet.microsoft.com/en-us/download/dotnet/8.0/runtime")

def get_screen_resolution():
    return root.winfo_screenwidth(), root.winfo_screenheight()

def setup_drag_and_drop():
    def drop(event, action):
        dropped_item = os.path.abspath(event.data.strip('{}'))  # normalize path
        if action == "create_pak":
            bat_path = os.path.join(get_script_directory(), "Files", "UnrealPak-Without-Compression.bat")
            if os.path.exists(bat_path):
                subprocess.Popen([bat_path, dropped_item], shell=True)
            else:
                messagebox.showerror("Error", f"{bat_path} not found")
        elif action == "unpack_pak":
            bat_path = os.path.join(get_script_directory(), "Files", "UnrealUnpakM0VER.bat")
            if os.path.exists(bat_path):
                subprocess.Popen([bat_path, dropped_item], shell=True)
            else:
                messagebox.showerror("Error", f"{bat_path} not found")

    def create_drop_widget(frame, text, action, width=35, height=3, fg="#fc98de", bg="#198246"):
        screen_width, screen_height = get_screen_resolution()
        font_size = 10 if screen_width >= 1920 else 8
        dnd_widget = tk.Label(frame, text=text, width=width, height=height, relief="solid",
                              padx=10, pady=10, anchor="center",
                              font=("Segoe Script Bold", font_size),
                              fg=fg, bg=bg)
        dnd_widget.pack(pady=5)
        dnd_widget.drop_target_register(DND_FILES)
        dnd_widget.dnd_bind('<<Drop>>', lambda event: drop(event, action))

    # Parent frame under the Fix Model button
    pak_frame = tk.Frame(root, bg="#198246")
    pak_frame.place(relx=0.5, rely=0.75, anchor="n")  # position under button

    # Create folder drop frame
    create_frame = tk.Frame(pak_frame, bg="#198246")
    create_frame.pack(side=tk.LEFT, padx=10)
    create_drop_widget(create_frame, "Drop folder to make uncompressed .PAK", "create_pak")

    # Create unpack drop frame
    unpack_frame = tk.Frame(pak_frame, bg="#198246")
    unpack_frame.pack(side=tk.RIGHT, padx=10)
    create_drop_widget(unpack_frame, "Drop .PAK file to unpack", "unpack_pak")

POSITION_FILE = os.path.join(get_script_directory(), "Files", "window_position.txt")

def save_window_position():
    x = root.winfo_x()
    y = root.winfo_y()
    with open(POSITION_FILE, "w") as f:
        f.write(f"{x},{y}")

def load_window_position():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, "r") as f:
            pos = f.read().strip().split(",")
            if len(pos) == 2 and pos[0].isdigit() and pos[1].isdigit():
                return int(pos[0]), int(pos[1])
    return None

def show_credits():
    credits_win = tk.Toplevel(root)
    credits_win.title("Credits")
    credits_win.geometry("550x300")  # slightly taller for links
    credits_win.configure(bg="#2b2b2b")
    credits_win.resizable(False, False)

    # Center the window
    credits_win.update_idletasks()
    w = 550
    h = 300
    screen_w = credits_win.winfo_screenwidth()
    screen_h = credits_win.winfo_screenheight()
    x = (screen_w // 2) - (w // 2)
    y = (screen_h // 2) - (h // 2)
    credits_win.geometry(f"{w}x{h}+{x}+{y}")

    # Title
    title = tk.Label(
        credits_win,
        text="Credits",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="#2b2b2b"
    )
    title.pack(pady=(10,5))

    # Frame for credits text and links
    content_frame = tk.Frame(credits_win, bg="#2b2b2b")
    content_frame.pack(expand=True, fill="both", padx=10, pady=5)

    # Credit text
    credits_text = tk.Text(
        credits_win,
        wrap="word",
        font=("Segoe UI", 10),
        fg="white",
        bg="#2b2b2b",
        borderwidth=0,
        highlightthickness=0
    )
    credits_text.insert("1.0",
        "Special thanks to:\n"
        "- ITSM0VER: Made UI for this tool & helped with research.\n"
        "- hypermodule: For making this all possible, wrote the script to make models work again!\n"
        "- RoRoGothic: Helped in many ways!\n\n"
        "Thanks to everyone who helped create, test and support this tool!"
    )
    credits_text.config(state="disabled")
    credits_text.pack(expand=False, fill="x")  # leave space below

def show_info():
    info_win = tk.Toplevel(root)
    info_win.title("Info")
    info_win.geometry("550x300")
    info_win.configure(bg="#2b2b2b")
    info_win.resizable(False, False)

    # Center the window
    info_win.update_idletasks()
    w = 550
    h = 300
    screen_w = info_win.winfo_screenwidth()
    screen_h = info_win.winfo_screenheight()
    x = (screen_w // 2) - (w // 2)
    y = (screen_h // 2) - (h // 2)
    info_win.geometry(f"{w}x{h}+{x}+{y}")

    # Title
    title = tk.Label(
        info_win,
        text="Info",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="#2b2b2b"
    )
    title.pack(pady=(10,5))

    # Frame for info text and links
    content_frame = tk.Frame(info_win, bg="#2b2b2b")
    content_frame.pack(expand=True, fill="both", padx=10, pady=(0,5))

    # Text content
    info_text = tk.Text(
        info_win,
        wrap="word",
        font=("Segoe UI", 10),
        fg="white",
        bg="#2b2b2b",
        borderwidth=0,
        highlightthickness=0
    )
    info_text.insert("1.0",
        "Welcome to Model Fixer!\n\n"
        "How to use model fixer:\n"
        "- Click 'Fix Model' to repair a model with serialisation error.\n"
        "- Choose the uasset file (with uexp in the same folder).\n\n"

        "How to use packaging:\n"
        "- Drag a folder onto the first box to create an uncompressed .PAK.\n"
        "- Drag a .PAK file onto the second box to unpack it.\n\n"
        "Make sure .NET 8.0 Runtime is installed and files are in the correct folders."
    )
    info_text.config(state="disabled")
    info_text.pack(expand=True, fill="both", padx=10, pady=5)

    # Function to open URLs
    def open_url(url):
        webbrowser.open(url)

    # Mesh Remover Link
    aib_label = tk.Label(
        content_frame,
        text="GTA DE MeshAibRemover GitHub",
        font=("Segoe UI", 9, "underline"),
        fg="#4a90e2",
        bg="#2b2b2b",
        cursor="hand2"
    )
    aib_label.pack(pady=(2,0))
    aib_label.bind("<Button-1>", lambda e: open_url("https://github.com/hypermodule/MeshAibRemover"))

    # Links directly under the thank-you message
    cue4_label = tk.Label(
        content_frame,
        text="CUE4Parse GitHub",
        font=("Segoe UI", 9, "underline"),
        fg="#4a90e2",
        bg="#2b2b2b",
        cursor="hand2"
    )
    cue4_label.pack(pady=(2,0))
    cue4_label.bind("<Button-1>", lambda e: open_url("https://github.com/FabianFG/CUE4Parse"))

    # UnrealPak GitHub link
    unrealpak_label = tk.Label(
        content_frame,
        text="UnrealPak GitHub",
        font=("Segoe UI", 9, "underline"),
        fg="#4a90e2",
        bg="#2b2b2b",
        cursor="hand2"
    )
    unrealpak_label.pack(pady=(2,0))
    unrealpak_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/xamarth/unrealpak"))

def open_link():
    webbrowser.open("https://next.nexusmods.com/profile/ITSM0VER/mods")  # Replace with your URL

def on_closing():
    save_window_position()  # Save the last window position
    root.destroy()          # Close the app

# Call this immediately after defining get_script_directory()
ensure_files_folder()

# --- UI setup ---
root = TkinterDnD.Tk() 
root.title("Model Fixer by ITSM0VER")
root.geometry("750x510")  # new width x height
root.configure(bg="#2b2b2b")  # dark background
root.resizable(False, False)

def load_pricedown_font(font_path):
    FR_PRIVATE = 0x10
    FR_NOT_ENUM = 0x20
    if os.path.exists(font_path):
        windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE | FR_NOT_ENUM, 0)
        return "Pricedown Bl"  # Internal font name from the font file
    return "Arial"  # fallback

pricedown_font_family = load_pricedown_font(
    os.path.join(get_script_directory(), "Files", ".Resources", "pricedown bl.otf")
)

# Path to your font file
font_path = os.path.join(get_script_directory(), "Files", ".Resources", "pricedown bl.otf")

# Load font from file with PIL
from PIL import ImageFont
font = ImageFont.truetype(font_path, 22)

# Path to the image
bg_path = os.path.join(get_script_directory(), "Files", ".Resources", "bk.png")
bg_image = Image.open(bg_path)

# Resize image to zoom out
window_width = 750
window_height = 450
scale = 1.2  # 80% zoom out
new_width = int(window_width * scale)
new_height = int(window_height * scale)
bg_image = bg_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Convert to Tkinter image
bg_photo = ImageTk.PhotoImage(bg_image)

# Place in a label
bg_label = tk.Label(root, image=bg_photo, bg="#2b2b2b")
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

#Icon
icon_path = os.path.join(get_script_directory(), "Files", ".Resources", "icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)


# --- Menu bar setup ---
menubar = tk.Menu(root)

# File menu
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Create Desktop Shortcut", command=lambda: create_desktop_shortcut())
file_menu.add_command(label="Exit", command=on_closing)  # You can add more later
menubar.add_cascade(label="File", menu=file_menu)

# Help menu
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="Info", command=show_info)
help_menu.add_command(label="Credits", command=show_credits)
help_menu.add_command(label=".NET 8.0 Download", command=open_dotnet_download)
help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Model Fixer v1.0\nby ITSM0VER"))
menubar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menubar)

# Restore last position
last_pos = load_window_position()
if last_pos:
    root.geometry(f"+{last_pos[0]}+{last_pos[1]}")  # only position, keep current size

# Save position on close
root.protocol("WM_DELETE_WINDOW", on_closing)

# ttk styling
style = ttk.Style()
style.theme_use("clam")  # modern base theme

# Style for normal button
style.configure(
    "Fix.TButton",
    font=("Segoe UI", 12, "bold"),
    foreground="white",
    background="#4a90e2",
    padding=10,
    borderwidth=0
)

# Hover effect
style.map(
    "Fix.TButton",
    background=[("active", "#357ABD")],  # darker blue on hover
    foreground=[("active", "white")]
)

# Display your photo at the top
img_path = os.path.join(get_script_directory(), "Files", ".Resources", "M0VER.png")
img = Image.open(img_path)
img = img.resize((120, 120), Image.Resampling.LANCZOS)
photo = ImageTk.PhotoImage(img)
img_label = tk.Label(root, image=photo, bg="#2b2b2b", cursor="hand2")  # hand cursor
img_label.image = photo
img_label.place(relx=0.5, rely=0.25, anchor="center")

# Make it clickable
img_label.bind("<Button-1>", lambda e: open_link())

# Place your Fix Model button below the image
def on_enter(e):
    btn_canvas.itemconfig(polygon, fill="#2ecc71")  # brighter green

def on_leave(e):
    btn_canvas.itemconfig(polygon, fill="#27ae60")  # normal green

def run_fix_model_clicked():
    run_fix_model()  # your existing function

# Place button canvas, but no bg color
btn_canvas = tk.Canvas(root, width=200, height=60, highlightthickness=0, bd=0)
btn_canvas.place(relx=0.5, rely=0.6, anchor="center")

# Set the background image (same bg you used in the app)
bg_subimage = bg_photo  # reuse the PhotoImage
btn_canvas.create_image(0, 0, image=bg_subimage, anchor="nw")

# Initially invisible polygon (transparent)
polygon = btn_canvas.create_polygon(
    15, 0, 185, 0, 170, 50, 0, 50,  # wider and taller
    fill="",       # fully transparent
    outline="",    # no border
    width=2
)

# Shadow text
shadow = btn_canvas.create_text(
    100, 25,
    text="Fix Model",
    fill="black",
    font=("Pricedown bl", 22, "bold")  # use registered font
)

# Main text
text = btn_canvas.create_text(
    98, 23,
    text="Fix Model",
    fill="#ff5fc0",
    font=("Pricedown bl", 22, "bold")
)

# Hover effect functions
def on_enter(e):
    btn_canvas.itemconfig(polygon, fill="#27ae60", outline="#000000")  # green fill with black border
    btn_canvas.itemconfig(shadow, fill="black")

def on_leave(e):
    btn_canvas.itemconfig(polygon, fill="", outline="")  # fully invisible again
    btn_canvas.itemconfig(text, fill="#ff5fc0")
    btn_canvas.itemconfig(shadow, fill="black")

# Bind hover/click to text, shadow, and polygon
for item in (text, shadow, polygon):
    btn_canvas.tag_bind(item, "<Enter>", lambda e: [on_enter(e), btn_canvas.config(cursor="hand2")])
    btn_canvas.tag_bind(item, "<Leave>", lambda e: [on_leave(e), btn_canvas.config(cursor="")])
    btn_canvas.tag_bind(item, "<Button-1>", lambda e: run_fix_model_clicked())

# Watermark label
watermark = tk.Label(
    root,
    text="UI Made by ITSM0VER",
    font=("Segoe UI", 8, "italic"),
    fg="#AAAAAA",        # light gray text
    bg="#2b2b2b"         # match window background
)
watermark.pack(side="bottom", pady=5)

setup_drag_and_drop()

root.mainloop()
