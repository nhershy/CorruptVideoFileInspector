import csv
import os
import subprocess
import sys
import tkinter as tk
import shlex
import traceback
from threading import Thread
from tkinter import filedialog
from datetime import datetime

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']

# ========================= FUNCTIONS ==========================

def selectDirectory(root):
    root.withdraw()
    return filedialog.askdirectory()

def countAllVideoFiles(dir):
    total = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(tuple(VIDEO_EXTENSIONS)):
                total += 1
    return total


def estimatedTime(total_videos):
    # estimating 3 mins per 2GB video file, on average
    total_minutes = total_videos * 3
    # Get hours with floor division
    hours = total_minutes // 60
    # Get additional minutes with modulus
    minutes = total_minutes % 60
    # Create time as a string
    time_string = "{} hours, {} minutes".format(hours, minutes)
    return time_string


def calculateProgress(count, total):
    return "{0}%".format(int((count / total) * 100))

def inspectVideoFiles(directory, tkinter_window, listbox_completed_videos, index_start, log_file):
    try:
        # CSV Results file
        results_file_path = os.path.join(directory, '_Results.csv')
        results_file_exists = os.path.isfile(results_file_path)
        if results_file_exists:
            os.remove(results_file_path)

        results_file = open(results_file_path, 'a+', encoding="utf8", newline='')
        results_file_writer = csv.writer(results_file)

        header = ['Video File', 'Corrupted']
        results_file_writer.writerow(header)
        results_file.flush()

        # # Log file
        # log_file_path = os.path.join(directory, '_Logs.log')
        # log_file_exists = os.path.isfile(log_file_path)
        # if log_file_exists:
        #     os.remove(log_file_path)
        # log_file = open(log_file_path, 'a', encoding="utf8")

        # Information
        print('CORRUPT VIDEO FILE INSPECTOR')
        print('')
        log_file.write('CORRUPT VIDEO FILE INSPECTOR\n\n')

        totalVideoFiles = countAllVideoFiles(directory)

        print(f'Total video files to inspect: {totalVideoFiles}')
        print(f'Starting from video index: {index_start}')
        log_file.write(f'Total video files to inspect: {totalVideoFiles}\n')
        log_file.write(f'Starting from video index: {index_start}\n')

        start_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        print(f'Started: {start_time}')
        print('')
        log_file.write(f'Started: {start_time}\n\n')
        log_file.flush()

        count = 0
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(tuple(VIDEO_EXTENSIONS)):
                    if (index_start > count + 1):
                        count += 1
                        continue

                    print(f'PROCESSING: {filename}...')
                    log_file.write(f'PROCESSING: {filename}\n')
                    log_file.flush()

                    global g_progress
                    g_progress.set(calculateProgress(count, totalVideoFiles))
                    tkinter_window.update()

                    global g_count
                    g_count.set(f"{count+1} / {totalVideoFiles}")
                    tkinter_window.update()

                    global g_currently_processing
                    g_currently_processing.set(filename)
                    tkinter_window.update()

                    abs_file_path = os.path.join(root, filename)

                    proc = subprocess.Popen(f'./ffmpeg -v error -i {shlex.quote(abs_file_path)} -f null - 2>&1', shell=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    output, error = proc.communicate()

                    # if proc.returncode != 0:
                    #     log_file.write(f'Output of "ffmpeg": {output}\n')
                    #     log_file.write(f'ERROR in "ffmpeg": {error}\n')
                    #     log_file.flush()

                    row_index = count
                    if (index_start != 1):
                        row_index = (count + 1) - index_start

                    row = ''
                    if not output:
                        # Healthy
                        print("\033[92m{0}\033[00m".format("  HEALTHY -> {}".format(filename)), end='\n')  # red
                        log_file.write(f'  HEALTHY -> {filename}\n')
                        log_file.flush()
                        row = [filename, 0]
                        listbox_completed_videos.insert(tk.END, filename)
                        listbox_completed_videos.itemconfig(row_index, bg='green')
                        tkinter_window.update()
                    else:
                        # Corrupt
                        print("\033[31m{0}\033[00m".format("  CORRUPTED -> {}".format(filename)), end='\n')  # red
                        log_file.write(f'  CORRUPTED -> {filename}\n')
                        log_file.flush()
                        row = [filename, 1]
                        listbox_completed_videos.insert(tk.END, filename)
                        listbox_completed_videos.itemconfig(row_index, bg='red')
                        tkinter_window.update()

                    results_file_writer.writerow(row)
                    results_file.flush()

                    count += 1

                    g_progress.set(calculateProgress(count, totalVideoFiles))
                    tkinter_window.update()

        results_file.flush()
        results_file.close()

        end_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        print(f'Finished: {end_time}')
        log_file.write(f'Ended: {end_time}\n\n')
        log_file.flush()
        log_file.close()
    except Exception as e:
        log_file.write(f'ERROR in "inspectVideoFiles" (aka main thread): {e}\n')
        log_file.flush()

def start_program(directory, root, index_start, index_selector_window, log_file):
    try:
        # GUI
        index_selector_window.withdraw()
        root.deiconify()

        label_progress_text = tk.Label(root, text="Progress:", font=('Helvetica Bold', 18))
        label_progress_text.pack(fill=tk.X, pady=10)

        g_progress.set("0%")
        label_progress_var = tk.Label(root, textvariable=g_progress, font=('Helvetica', 50))
        label_progress_var.pack(fill=tk.X, pady=(0, 10))

        g_count.set("0 / 0")
        label_count_var = tk.Label(root, textvariable=g_count, font=('Helvetica', 16))
        label_count_var.pack(fill=tk.X, pady=(0, 20))

        label_currently_processing_text = tk.Label(root, text="Currently Processing:", font=('Helvetica Bold', 18))
        label_currently_processing_text.pack(fill=tk.X, pady=10)

        g_currently_processing.set("N/A")
        label_currently_processing_var = tk.Label(root, textvariable=g_currently_processing, font=('Helvetica', 16))
        label_currently_processing_var.pack(fill=tk.X, pady=(0, 10))

        listbox_completed_videos = tk.Listbox(root, font=('Helvetica', 16))
        listbox_completed_videos.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        scrollbar = tk.Scrollbar(root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
        listbox_completed_videos.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox_completed_videos.yview)

        thread = Thread(target=inspectVideoFiles, args=(directory, root, listbox_completed_videos, index_start, log_file))
        thread.start()
    except Exception as e:
        log_file.write(f'ERROR in "start_program": {e}\n\n')
        log_file.flush()

# ========================= MAIN ==========================

root = tk.Tk()
root.resizable(False, False)
root.geometry("400x500")
root.title("Corrupt Video Inspector")
g_progress = tk.StringVar()
g_count = tk.StringVar()
g_currently_processing = tk.StringVar()

directory = selectDirectory(root)

# Log file
log_file_path = os.path.join(directory, '_Logs.log')
log_file_exists = os.path.isfile(log_file_path)
if log_file_exists:
    os.remove(log_file_path)
log_file = open(log_file_path, 'a', encoding="utf8")

totalVideos = countAllVideoFiles(directory)

index_selector_window = tk.Toplevel(root)
index_selector_window.resizable(False, False)
index_selector_window.geometry("300x400")
index_selector_window.title("Corrupt Video Inspector")
label_video_count = tk.Label(index_selector_window, text="Total number of videos:", font=('Helvetica Bold', 18))
label_video_count.pack(fill=tk.X, pady=5)
label_video_count_var = tk.Label(index_selector_window, text=f"{totalVideos}", font=('Helvetica', 16))
label_video_count_var.pack(fill=tk.X, pady=(5, 20))
label_index_start = tk.Label(index_selector_window, text=f"Start at video index (1 - {countAllVideoFiles(directory)}):", font=('Helvetica Bold', 18))
label_index_start.pack(fill=tk.X, pady=5)
entry_index_input = tk.Entry(index_selector_window, width=50)
entry_index_input.focus_set()
entry_index_input.insert(tk.END, '1')
entry_index_input.pack(fill=tk.X, padx=40)
label_explanation = tk.Label(index_selector_window, wraplength=250, text="The default is '1'. Set index to '1' if you want to start from the beginning and process all videos. If you are resuming a previous operation, then set the index to the desired number. Also note, each run will overwrite the _Logs and _Results files.", font=('Helvetica Italic', 12))
label_explanation.pack(fill=tk.X, pady=5, padx=20)
button_start = tk.Button(index_selector_window, text="Start", width=20, command=lambda : start_program(directory, root, int(entry_index_input.get()), index_selector_window, log_file))
button_start.pack(pady=20)

root.mainloop()