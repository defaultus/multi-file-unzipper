import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import os
from tkinter import ttk
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *

executor = ThreadPoolExecutor(max_workers=10)
running_futures = []
lock = threading.Lock()

# function to prompt the user to select a folder.
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_selected)
        # writed the path to the saved_path text file
        saved_path_file = get_saved_path()
        saved_path_contents = saved_path_file.read_text()
        saved_path_file.write_text(folder_selected)

# function to check for a file and return it (if it doesn't exist it will create it).
def get_saved_path() -> Path:
    saved_path_file = Path("savedPath.txt")
    if not saved_path_file.exists(): # check the folder it is in for the file, if not it creates it.
        saved_path_file.write_text("")
    return saved_path_file # returns the file object

# function returns a list of filepaths (.zip, .rar, .7z)
# i haven't really come across another compression type but im pretty sure it can be added easily 
def get_files(dir: Path) -> list[Path]:
    archive_ext = ["zip", "rar", "7z"]
    archive_files = []
    for file_name in os.listdir(dir):
        ext = file_name.split(".")[-1].lower()
        if ext in archive_ext:
            archive_files.append(os.path.join(dir, file_name))
    return archive_files

def extract(archive_file, output_folder):
    subprocess.run(["7z", "x", archive_file, f"-o{output_folder}"], check=True)

# function to unzip files using 7zip cli tool and multi-threading
def start_unzip():
    label_loading.config(text="UNZIPPING...")
    archive_folder = Path(path_entry.get())
    output_folder = Path.joinpath(archive_folder, "opened")
    
    # checking and or creating a output folder for unzipped folders
    output = Path.joinpath(archive_folder, "output")
    if not output.exists():
        output.mkdir(parents=False, exist_ok=True)
    archive_file_list = get_files(archive_folder)

    with lock:
        running_futures.clear()
        for file in archive_file_list:
            future = executor.submit(extract, file, output)
            running_futures.append(future)

    check_unzip_complete(archive_file_list)

def check_unzip_complete(archive_folder_list: list[Path]):
    with lock:
        if all(f.done() for f in running_futures):
            if boolvar.get():
                label_loading.config(text="REMOVING FILES")
                for file in archive_folder_list:
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Error removing {file}: {e}")
            label_loading.config(text="FINISHED")
            start_unzip_btn.config(state="normal")
            return
    window.after(500, lambda: check_unzip_complete(archive_folder_list))

# yell at the user is there are still threads running, then close when done
def on_close():
    with lock:
        if any(not futures.done() for futures in running_futures): # checks if tthere are unfinished threads
            ttk.messagebox.showinfo("Please wait", "Extraction is still running. Please wait before closing.")
            return
        window.destroy()
    

# window stuff
window = tb.Window(themename="darkly")
window.title("multi-file unzipper")
window.geometry("600x400")
window.protocol("WM_DELETE_WINDOW", on_close)

# content
label1 = tb.Label(window, text="1. enter the path of your folder filled with archives.")
label1.pack(pady=5)
ttk.Label(window, text="(NOTE: in browse you will not see the archive files!)").pack(pady=5)

path_entry = tb.Entry(window, width=50)
path_entry.pack(pady=5)

# check for a file that would contain a path (so the same user doesn't have to do this more than once).
saved_path_file = get_saved_path()
saved_path_contents = saved_path_file.read_text()
if not saved_path_contents == "":
    path_entry.insert(0, saved_path_contents)

browse_button = tb.Button(window, text="browse folders", command=browse_folder)
browse_button.pack(pady=5)

boolvar = tk.BooleanVar()
tick_box = tb.Checkbutton(window, text="tick to remove archive files after operation.", variable=boolvar)
tick_box.pack(pady=5)

label3 = tb.Label(window, text="3. Press 'Start Unzip' to start unzipping all archive files inside the selected folder.")
label3.pack(pady=5)

# button to start multiple threads to unzip all files.
# asyncio is proabably a bit overkill, this wasn't designed to handle an increcdible amount of files.
# this is meant for around 10 archive files at once, if more were to be handled asyncio would probably be nice.
start_unzip_btn = tb.Button(window, text="Start Unzip", command=start_unzip)
start_unzip_btn.pack(pady=5)

label_loading = tb.Label(window, text="")

window.mainloop()
