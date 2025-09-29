import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox, filedialog, colorchooser, Toplevel, Label
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import subprocess
import sys
import webbrowser
from PIL import Image, ImageTk, ImageFont
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
import pyperclip
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    file_paths = filedialog.askopenfilenames(
        title="Select UAsset files",
        filetypes=[("UAsset Files", "*.uasset")]
    )

    if not file_paths:
        return

    exe_path = os.path.join(get_script_directory(), "Files", "MeshAibRemover.exe")
    if not os.path.exists(exe_path):
        messagebox.showerror("Error", f"MeshAibRemover.exe not found:\n{exe_path}")
        return

    def run_file(file_path):
        try:
            subprocess.run([exe_path, file_path], check=True)
            print(f"✅ Fixed {file_path}")
        except Exception as e:
            print(f"❌ Failed {file_path} ({e})")

    # Run files in background threads
    def background_task():
        max_workers = 5
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_file, fp) for fp in file_paths]
            # Wait for all futures to complete
            for future in as_completed(futures):
                pass

        # Notify user when done
        messagebox.showinfo("Model Fixer", f"Finished processing {len(file_paths)} file(s). Check console for details.")

    threading.Thread(target=background_task, daemon=True).start()

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

    # Set the app icon for this Toplevel window
    credits_win.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

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

    # Set the app icon for this Toplevel window
    info_win.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

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
    webbrowser.open("https://next.nexusmods.com/profile/ITSM0VER/mods")  # URL Link

def on_closing():
    save_window_position()  # Save the last window position
    root.destroy()          # Close the app

# Call this to ensure the files folder exists
ensure_files_folder()

def open_image_picker_window(parent=None):
    def open_image():
        nonlocal original_image, scale_ratio, img_pos_x, img_pos_y, photo

        picker_window.attributes("-topmost", False)
        picker_window.update()

        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            original_image = Image.open(file_path)

            # Reset zoom & position
            scale_ratio = min(canvas_width / original_image.width, canvas_height / original_image.height, 1)
            new_w, new_h = int(original_image.width * scale_ratio), int(original_image.height * scale_ratio)
            img_pos_x = (canvas_width - new_w) // 2
            img_pos_y = (canvas_height - new_h) // 2
            update_image()

            picker_window.attributes("-topmost", True)
            picker_window.update()

    def display_image(img, x, y):
        canvas.delete("all")
        canvas.config(width=canvas_width, height=canvas_height)
        canvas.create_image(x, y, anchor=tk.NW, image=img)
        canvas.image = img

    def get_pixel_color(event):
        if original_image is not None:
            img_x = event.x - img_pos_x
            img_y = event.y - img_pos_y
            if 0 <= img_x < original_image.width * scale_ratio and 0 <= img_y < original_image.height * scale_ratio:
                orig_x = int(img_x / scale_ratio)
                orig_y = int(img_y / scale_ratio)
                pixel_color_rgb = original_image.getpixel((orig_x, orig_y))
                pixel_color_hex = f"#{pixel_color_rgb[0]:02x}{pixel_color_rgb[1]:02x}{pixel_color_rgb[2]:02x}"
                rgb_label.config(text=f"RGBA: {pixel_color_rgb}")
                hex_label.config(text=f"HEX: {pixel_color_hex}")

    def copy_color_hex():
        hex_value = hex_label.cget("text").split(": ")[1]
        pyperclip.copy(hex_value)

    def update_image(center_x=None, center_y=None):
        nonlocal photo, img_pos_x, img_pos_y
        if original_image is None:
            return

        scale_ratio_clamped = max(0.1, min(scale_ratio, 5.0))
        new_width = int(original_image.width * scale_ratio_clamped)
        new_height = int(original_image.height * scale_ratio_clamped)
        resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)

        # Keep zoom centered on given point or canvas center
        if center_x is None or center_y is None:
            center_x, center_y = canvas_width // 2, canvas_height // 2
        # Current image coords relative to zoom point
        rel_x = (center_x - img_pos_x) / (original_image.width * scale_ratio)
        rel_y = (center_y - img_pos_y) / (original_image.height * scale_ratio)
        # New top-left
        img_pos_x = int(center_x - rel_x * new_width)
        img_pos_y = int(center_y - rel_y * new_height)

        display_image(photo, img_pos_x, img_pos_y)

    def zoom(event):
        nonlocal scale_ratio
        factor = 1.1 if event.delta > 0 else 0.9
        scale_ratio *= factor
        update_image(event.x, event.y)

    def start_pan(event):
        nonlocal pan_start_x, pan_start_y
        pan_start_x = event.x
        pan_start_y = event.y

    def do_pan(event):
        nonlocal img_pos_x, img_pos_y, pan_start_x, pan_start_y
        dx = event.x - pan_start_x
        dy = event.y - pan_start_y
        img_pos_x += dx
        img_pos_y += dy
        pan_start_x = event.x
        pan_start_y = event.y
        display_image(photo, img_pos_x, img_pos_y)

    # Create Toplevel
    picker_window = tk.Toplevel(parent)
    picker_window.title("Image Color Picker")
    picker_window.configure(bg="#2b2b2b")
    picker_window.attributes("-topmost", True)
    window_width, window_height = 650, 700
    picker_window.geometry(f"{window_width}x{window_height}")
    picker_window.resizable(False, False)
    picker_window.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

    # Center window
    screen_width = picker_window.winfo_screenwidth()
    screen_height = picker_window.winfo_screenheight()
    pos_x = (screen_width - window_width) // 2
    pos_y = (screen_height - window_height) // 2
    picker_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    # Canvas
    canvas_width, canvas_height = 600, 500
    canvas = tk.Canvas(picker_window, width=canvas_width, height=canvas_height, bg="#1f1f1f", cursor="pencil")
    canvas.pack(pady=10)

    # Labels
    rgb_label = tk.Label(picker_window, text="RGBA: ", font=("Segoe UI", 10), fg="white", bg="#2b2b2b")
    rgb_label.pack(pady=2)
    hex_label = tk.Label(picker_window, text="HEX: ", font=("Segoe UI", 10), fg="white", bg="#2b2b2b")
    hex_label.pack(pady=2)

    # Buttons
    button_frame = ttk.Frame(picker_window)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    open_button = ttk.Button(button_frame, text="Open Image", command=open_image, cursor="hand2")
    open_button.pack(side=tk.LEFT, padx=5, pady=5)

    copy_button = ttk.Button(button_frame, text="Copy Color #", command=copy_color_hex, cursor="hand2")
    copy_button.pack(side=tk.LEFT, padx=5, pady=5)

    #zoom_in_button = ttk.Button(button_frame, text="+", command=lambda: [scale_ratio:=scale_ratio*1.1, update_image()], width=3, cursor="hand2")
    #zoom_in_button.pack(side=tk.LEFT, padx=5, pady=5)

    #zoom_out_button = ttk.Button(button_frame, text="-", command=lambda: [scale_ratio:=scale_ratio/1.1, update_image()], width=3, cursor="hand2")
    #zoom_out_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Variables
    photo = None
    original_image = None
    scale_ratio = 1.0
    img_pos_x = 0
    img_pos_y = 0
    pan_start_x = 0
    pan_start_y = 0

    # Left-click: pick color
    canvas.bind("<Button-1>", get_pixel_color)

    # Right-click: start panning
    canvas.bind("<ButtonPress-3>", start_pan)
    canvas.bind("<B3-Motion>", do_pan)

    # Zoom with mouse wheel
    canvas.bind("<MouseWheel>", zoom)  # Windows
    canvas.bind("<Button-4>", lambda e: [scale_ratio:=scale_ratio*1.1, update_image()])  # Linux scroll up
    canvas.bind("<Button-5>", lambda e: [scale_ratio:=scale_ratio/1.1, update_image()])  # Linux scroll down

    picker_window.wait_window()

def show_links():
    links = [
        ("Tutorials Index", "https://gtaforums.com/topic/982746-gta-definitive-trilogy-tutorials-index/"),
        ("LC.net Tutorial", "https://libertycity.net/gta-the-trilogy/articles/5194-how-to-create-mods-for-gta-the-trilogy.html"),
        ("Modding the NSwitch Version", "https://www.reddit.com/r/GTATrilogyMods/comments/qwzkcc/modding_for_the_nintendo_switch_version/"),
        ("Texture Modding Guide", "https://gtaforums.com/topic/977439-gtasade-texture-modding-guide/"),
        ("Sound Modding Guide", "https://gtaforums.com/topic/910487-gta-sa-guide-for-making-car-sound-mods/"),
        ("Localization Modding Guide", "https://gtaforums.com/topic/977646-gtasade-localization-modding-guide/"),
        ("Vehicle Modding Guide", "https://video.wixstatic.com/video/4db758_7b8a302870994003b449e45b1de60f06/1080p/mp4/file.mp4")
    ]

    links_window = tk.Toplevel(root)
    links_window.title("Helpful Links")
    links_window.resizable(False, False)
    links_window.configure(bg="#2b2b2b")
    links_window.wm_attributes("-topmost", 1)

    # Set the app icon for this Toplevel window
    links_window.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

    # Fixed size & center
    window_width, window_height = 650, 320
    screen_width = links_window.winfo_screenwidth()
    screen_height = links_window.winfo_screenheight()
    position_x = (screen_width - window_width) // 2
    position_y = (screen_height - window_height) // 2
    links_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    # Title label
    title_label = tk.Label(
        links_window,
        text="Helpful GTA DE Modding Links",
        font=("Segoe UI", 14, "bold"),
        bg="#2b2b2b",
        fg="white"
    )
    title_label.pack(pady=(10, 5))

    # Frame for text + scrollbar
    frame = tk.Frame(links_window, bg="#2b2b2b")
    frame.pack(expand=1, fill="both", padx=10, pady=(0,10))

    # Text widget
    text_widget = tk.Text(
        frame,
        wrap="word",
        bg="#2b2b2b",
        fg="white",
        font=("Segoe UI", 10),
        borderwidth=0,
        highlightthickness=0
    )
    text_widget.pack(side="left", expand=1, fill="both")

    # Scrollbar
    scrollbar = ttk.Scrollbar(frame, command=text_widget.yview)
    scrollbar.pack(side="right", fill="y")
    text_widget.config(yscrollcommand=scrollbar.set)

    text_widget.insert(tk.END, "Helpful Links:\n\n")

    for description, url in links:
        text_widget.insert(tk.END, f"{description}\n", "desc")
        start = text_widget.index(tk.INSERT)
        text_widget.insert(tk.END, f"{url}\n\n", "link")
        end = text_widget.index(tk.INSERT)
        text_widget.tag_add("link", start, end)

    # Styling
    text_widget.tag_configure("link", foreground="#4a90e2", underline=True)
    text_widget.tag_configure("desc", foreground="white", font=("Segoe UI", 10, "bold"))

    # Link behavior
    def open_url(event):
        start, end = text_widget.tag_prevrange("link", text_widget.index(tk.CURRENT))
        url = text_widget.get(start, end)
        webbrowser.open_new(url)

    text_widget.tag_bind("link", "<Button-1>", open_url)
    text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.config(cursor=""))

    text_widget.config(state=tk.DISABLED)

def update_color():
    r = red_scale.get()
    g = green_scale.get()
    b = blue_scale.get()
    hex_color = f'#{r:02x}{g:02x}{b:02x}'.upper()
    # Update color display (tk.Label)
    color_display.config(bg=hex_color)
    color_code.set(f'RGB({r}, {g}, {b}) / {hex_color}')
    hex_entry_var.set(hex_color)

def choose_color():
    global color_display, red_scale, green_scale, blue_scale, color_code, color_picker_window
    
    # Hide color_picker_window
    color_picker_window.withdraw()
    
    # Open color chooser dialog
    chosen_color = colorchooser.askcolor(title="Choose color", initialcolor="#000000")
    
    if chosen_color[1] is not None:  # Check if a color was actually chosen
        rgb_values = chosen_color[0]  # RGB values are in chosen_color[0]
        red_scale.set(int(rgb_values[0]))
        green_scale.set(int(rgb_values[1]))
        blue_scale.set(int(rgb_values[2]))
        update_color()
        
    # Bring the color picker window back
    color_picker_window.deiconify()
    color_picker_window.lift()
    color_picker_window.focus_force()

def copy_color_decimal():
    # Get the current hex color code from color_code
    hex_code = color_code.get().split(' / ')[-1]
    
    # Copy the hex code to clipboard
    color_picker_window.clipboard_clear()
    color_picker_window.clipboard_append(hex_code)
    color_picker_window.update()  # Manually update clipboard

def update_from_hex(event=None):
    hex_color = hex_entry_var.get()
    if len(hex_color) == 7 and hex_color[0] == '#':
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            red_scale.set(r)
            green_scale.set(g)
            blue_scale.set(b)
            update_color()
        except ValueError:
            pass

def open_color_picker_window(parent=None):
    global color_display, red_scale, green_scale, blue_scale, color_code, color_picker_window, hex_entry_var

    # Create the window
    color_picker_window = tk.Toplevel(parent)
    color_picker_window.title("Color Codes")
    color_picker_window.configure(bg="#2b2b2b")  # Dark background
    color_picker_window.attributes('-topmost', True)
    window_width, window_height = 320, 280
    color_picker_window.geometry(f"{window_width}x{window_height}")
    color_picker_window.resizable(False, False)

    # Set the app icon for this Toplevel window
    color_picker_window.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

    # Center the window
    screen_width = color_picker_window.winfo_screenwidth()
    screen_height = color_picker_window.winfo_screenheight()
    position_x = (screen_width - window_width) // 2
    position_y = (screen_height - window_height) // 2
    color_picker_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    # Color display
    color_display = tk.Label(
        color_picker_window,
        text="Color Display",
        width=20,
        height=5,
        bg="#1f1f1f",
        fg="white",
        relief="sunken",
        bd=2
    )
    color_display.grid(row=0, column=0, columnspan=3, pady=10)

    # RGB sliders
    slider_bg = "#2b2b2b"
    slider_fg = "#ff5fc0"
    red_scale = tk.Scale(color_picker_window, from_=0, to=255, orient=tk.HORIZONTAL, label="Red",
                         command=lambda x: update_color(), bg=slider_bg, fg=slider_fg, highlightbackground=slider_bg)
    red_scale.grid(row=1, column=0)
    green_scale = tk.Scale(color_picker_window, from_=0, to=255, orient=tk.HORIZONTAL, label="Green",
                           command=lambda x: update_color(), bg=slider_bg, fg=slider_fg, highlightbackground=slider_bg)
    green_scale.grid(row=1, column=1)
    blue_scale = tk.Scale(color_picker_window, from_=0, to=255, orient=tk.HORIZONTAL, label="Blue",
                          command=lambda x: update_color(), bg=slider_bg, fg=slider_fg, highlightbackground=slider_bg)
    blue_scale.grid(row=1, column=2)

    # Current color code display
    color_code = tk.StringVar()
    color_code.set("RGB(0, 0, 0) / #000000")
    color_code_label = tk.Label(
        color_picker_window,
        textvariable=color_code,
        bg="#2b2b2b",
        fg="white"
    )
    color_code_label.grid(row=2, column=0, columnspan=3, pady=5)

    # HEX entry
    hex_entry_var = tk.StringVar()
    hex_entry_var.set("")
    hex_entry = ttk.Entry(color_picker_window, textvariable=hex_entry_var, width=12)
    hex_entry.grid(row=3, column=0, columnspan=3, pady=5)
    hex_entry.bind("<Return>", update_from_hex)

    # Buttons
    choose_color_button = tk.Button(
        color_picker_window,
        text="Choose Color",
        command=choose_color,
        bg="#ff5fc0",
        fg="white",
        activebackground="#ff79d1",
        cursor="hand2"
    )
    choose_color_button.grid(row=4, column=0, pady=10, padx=5)

    # Spacer
    spacer = tk.Label(color_picker_window, width=5, bg="#2b2b2b")
    spacer.grid(row=4, column=1)

    copy_color_button = tk.Button(
        color_picker_window,
        text="Copy Color #",
        command=copy_color_decimal,
        bg="#ff5fc0",
        fg="white",
        activebackground="#ff79d1",
        cursor="hand2"
    )
    copy_color_button.grid(row=4, column=2, pady=10, padx=5)

def rgb_hex_to_float(color):
    if color.startswith('#'):
        color = color[1:]  # Remove the '#' if present
    
    if len(color) == 6:
        r = round(int(color[0:2], 16) / 255.0, 3)
        g = round(int(color[2:4], 16) / 255.0, 3)
        b = round(int(color[4:6], 16) / 255.0, 3)
        return (r, g, b, 1.0)  # Alpha is 1.0 for fully opaque
    elif len(color) == 3:
        r = round(int(color[0], 16) / 15.0, 3)
        g = round(int(color[1], 16) / 15.0, 3)
        b = round(int(color[2], 16) / 15.0, 3)
        return (r, g, b, 1.0)
    elif ',' in color:
        r, g, b = map(float, color.split(','))
        r = round(r / 255.0, 3)
        g = round(g / 255.0, 3)
        b = round(b / 255.0, 3)
        return (r, g, b, 1.0)  # Alpha is 1.0 for fully opaque
    else:
        raise ValueError("Invalid input format")

def open_converter(parent=None):
    def convert_color():
        input_color = entry.get().strip()
        try:
            result = rgb_hex_to_float(input_color)
            result_label.config(text=f"Converted result: {result}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def copy_to_clipboard():
        result = result_label.cget("text")
        if result.startswith("Converted result: "):
            result = result[len("Converted result: "):]
            result = result.strip("()")
            converter_window.clipboard_clear()
            converter_window.clipboard_append(result)

    # Create the converter window
    converter_window = tk.Toplevel(parent)
    converter_window.title("Converter")
    converter_window.resizable(False, False)
    converter_window.configure(bg="#2b2b2b")  # Dark theme
    converter_window.attributes("-topmost", True)
    window_width, window_height = 320, 180

    # Set the app icon for this Toplevel window
    converter_window.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

    # Center the window
    screen_width = converter_window.winfo_screenwidth()
    screen_height = converter_window.winfo_screenheight()
    position_x = (screen_width - window_width) // 2
    position_y = (screen_height - window_height) // 2
    converter_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    # Label
    label = tk.Label(converter_window, text="Enter RGB(0, 0, 0) / HEX(#000000) value:",
                     bg="#2b2b2b", fg="white")
    label.pack(pady=10)

    # Entry
    entry = ttk.Entry(converter_window, width=30)
    entry.pack()

    # Result frame
    result_frame = tk.Frame(converter_window, bg="#2b2b2b")
    result_frame.pack(pady=10)

    result_label = tk.Label(result_frame, text="Converted result will appear here",
                            bg="#2b2b2b", fg="white")
    result_label.pack(side=tk.LEFT)

    copy_button = tk.Button(result_frame, text="Copy", command=copy_to_clipboard,
                            bg="#ff5fc0", fg="white", activebackground="#ff79d1", cursor="hand2")
    copy_button.pack(side=tk.LEFT, padx=5)

    # Convert button
    convert_button = tk.Button(converter_window, text="Convert", command=convert_color,
                               bg="#ff5fc0", fg="white", activebackground="#ff79d1", cursor="hand2")
    convert_button.pack(pady=10)

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

# Path to font file
font_path = os.path.join(get_script_directory(), "Files", ".Resources", "pricedown bl.otf")

# Load font from file with PIL
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

def show_about():
    about_win = tk.Toplevel(root)
    about_win.title("About")
    about_win.configure(bg="#2b2b2b")
    about_win.resizable(False, False)

    # Center the window
    win_width = 300
    win_height = 150
    x = (root.winfo_screenwidth() // 2) - (win_width // 2)
    y = (root.winfo_screenheight() // 2) - (win_height // 2)
    about_win.geometry(f"{win_width}x{win_height}+{x}+{y}")

    # Set the app icon for this Toplevel window
    about_win.iconbitmap(os.path.join(get_script_directory(), "Files", ".Resources", "ICON.ico"))

    # About text
    tk.Label(
        about_win,
        text="Model Fixer v1.2\nby ITSM0VER",
        bg="#2b2b2b",
        fg="white",
        font=("Segoe UI", 12, "bold"),
        justify="center"
    ).pack(expand=True)

    # OK button
    tk.Button(
        about_win,
        text="OK",
        command=about_win.destroy,
        bg="#444444",
        fg="white",
        activebackground="#555555",
        activeforeground="white",
        relief="flat",
        width=10
    ).pack(pady=10)

# --- Custom dark menu bar ---
menu_frame = tk.Frame(root, bg="#2b2b2b", height=25)
menu_frame.pack(side="top", fill="x")

# Helper function to create dark Menubuttons
def create_dark_menubutton(parent, text, menu_items, font_size=10):
    btn = tk.Menubutton(
        parent,
        text=text,
        bg="#2b2b2b",
        fg="white",
        activebackground="#444444",
        activeforeground="white",
        relief="flat",
        font=("Segoe Script Bold", font_size),
        cursor="hand2"
    )
    menu = tk.Menu(btn, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#444444", activeforeground="white")
    for item in menu_items:
        if item == "separator":
            menu.add_separator()
        else:
            label, command = item
            menu.add_command(label=label, command=command)
    btn.config(menu=menu)
    btn.pack(side="left", padx=5)
    return btn

# File menu items
file_items = [
    ("Create Desktop Shortcut", create_desktop_shortcut),
    ("Exit", on_closing)
]

# Tools menu items
tools_items = [
    ("Image Color Picker", open_image_picker_window),
    ("RGB Color Codes", open_color_picker_window),
    ("RGB&HEX to float32 Converter", open_converter)
]

# Help menu items
help_items = [
    ("Info", show_info),
    "separator",
    ("Tutorial Links", show_links),
    "separator",
    ("Credits", show_credits),
    (".NET 8.0 Download", open_dotnet_download),
    ("About", show_about)
]

# Create the buttons
file_btn = create_dark_menubutton(menu_frame, "File", file_items)
tools_btn = create_dark_menubutton(menu_frame, "Tools", tools_items)
help_btn = create_dark_menubutton(menu_frame, "Help", help_items)

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

# Display photo at the top
img_path = os.path.join(get_script_directory(), "Files", ".Resources", "M0VER.png")
img = Image.open(img_path)
img = img.resize((120, 120), Image.Resampling.LANCZOS)
photo = ImageTk.PhotoImage(img)
img_label = tk.Label(root, image=photo, bg="#2b2b2b", cursor="hand2")  # hand cursor
img_label.image = photo
img_label.place(relx=0.5, rely=0.25, anchor="center")

# Make it clickable
img_label.bind("<Button-1>", lambda e: open_link())

# Place Fix Model button below the image
def on_enter(e):
    btn_canvas.itemconfig(polygon, fill="#2ecc71")  # brighter green

def on_leave(e):
    btn_canvas.itemconfig(polygon, fill="#27ae60")  # normal green

def run_fix_model_clicked():
    run_fix_model() #Fix that thang PACHOW xD

# Place button canvas, but no bg color
btn_canvas = tk.Canvas(root, width=230, height=60, highlightthickness=0, bd=0)
btn_canvas.place(relx=0.5, rely=0.6, anchor="center")

# Match canvas size
btn_width = 820
btn_height = 600

# Load + resize app background
bg_path = os.path.join(get_script_directory(), "Files", ".Resources", "bk.png")
bg_image = Image.open(bg_path).resize((btn_width, btn_height), Image.Resampling.LANCZOS)

# Convert to PhotoImage
bg_subimage = ImageTk.PhotoImage(bg_image)

# Draw on canvas
btn_canvas.create_image(0, 0, image=bg_subimage, anchor="nw")

# Keep a reference to stop garbage collection
btn_canvas.bg_ref = bg_subimage

# Amount to shift everything right
x_offset = 15  # increase to move further right

# Polygon (shifted)
polygon = btn_canvas.create_polygon(
    15 + x_offset, 0, 185 + x_offset, 0, 170 + x_offset, 50, 0 + x_offset, 50,
    fill="", outline="", width=2
)

# Shadow text (shifted)
shadow = btn_canvas.create_text(
    100 + x_offset, 25,
    text="Fix Model",
    fill="black",
    font=("Pricedown bl", 22, "bold")
)

# Main text (shifted)
text = btn_canvas.create_text(
    98 + x_offset, 23,
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
