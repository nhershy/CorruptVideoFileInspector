import csv
import os
import subprocess
import tkinter as tk
import shlex
import platform
import psutil
import signal
from threading import Thread
from tkinter import filedialog
from tkinter import ttk
from tkmacosx import Button as MacButton
from datetime import datetime

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']

# ========================= FUNCTIONS ==========================

def isMacOs():
    if 'Darwin' in platform.system():
        return True
    return False

def isWindowsOs():
    if 'Windows' in platform.system():
        return True
    return False

def isLinuxOs():
    if 'Linux' in platform.system():
        return True
    return False

def selectDirectory(root, label_select_directory, button_select_directory):
    # root.withdraw()
    directory = filedialog.askdirectory()

    if len(directory) > 0:
        label_select_directory.destroy()
        button_select_directory.destroy()
        afterDirectoryChosen(root, directory)

def countAllVideoFiles(dir):
    total = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                total += 1
    return total

def getAllVideoFiles(dir):
    index = 1
    videos_found_list = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                videos_found_list.append(f' {index}:  {file}')
                index += 1
    return videos_found_list

def verify_ffmpeg_still_running(root):
    ffmpeg_window = tk.Toplevel(root)
    ffmpeg_window.resizable(False, False)
    ffmpeg_window.geometry("400x150")
    ffmpeg_window.title("Verify ffmpeg Status")
    output = ''
    cpu_usage = ''

    if isMacOs():
        proc = subprocess.Popen("ps -Ao comm,pcpu -r | head -n 10 | grep ffmpeg", shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode('utf-8').strip()
        if "ffmpeg" in output:
            cpu_usage = output.split()[1]
            output = f"ffmpeg is currently running.\nffmpeg is currently using {cpu_usage}% of CPU"
        else:
            output = "ffmpeg is NOT currently running!"
    if isWindowsOs():
        found = False
        process_names = [proc for proc in psutil.process_iter()]
        for proc in process_names:
            if "ffmpeg" in proc.name():
                cpu_usage = proc.cpu_percent()
                found = True
                break
        if found:
            output = f"ffmpeg is currently running.\nffmpeg is currently using {cpu_usage}% of CPU"
        else:
            output = "ffmpeg is NOT currently running!"

    label_ffmpeg_result = tk.Label(ffmpeg_window, width=375, text=output, font=('Helvetica', 14))
    label_ffmpeg_result.pack(fill=tk.X, pady=20)

def kill_ffmpeg_warning(root):
    ffmpeg_kill_window = tk.Toplevel(root)
    ffmpeg_kill_window.resizable(False, False)
    ffmpeg_kill_window.geometry("400x300")
    ffmpeg_kill_window.title("Safely Quit Program")

    label_ffmpeg_kill = tk.Label(ffmpeg_kill_window, wraplength=375, width=375, text="This application spawns a subprocess named 'ffmpeg'. If this program is quit using the 'X' button, for example, the 'ffmpeg' subprocess will continue to run in the background of the host computer, draining the CPU resources. Clicking the button below will terminate the 'ffmpeg' subprocess and safely quit the application. This will prematurely end all video processing. Only do this if you want to safely exit the program and clean all subprocesses", font=('Helvetica', 14))
    label_ffmpeg_kill.pack(fill=tk.X, pady=20)

    if isMacOs():
        # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
        button_kill_ffmpeg = MacButton(ffmpeg_kill_window, background='#E34234', borderless=1, foreground='white', text="Terminate Program", width=500, command=lambda: kill_ffmpeg(root))
        button_kill_ffmpeg.pack(pady=10)
    elif isWindowsOs():
        button_kill_ffmpeg = tk.Button(ffmpeg_kill_window, background='#E34234', foreground='white', text="Terminate Program", width=200, command=lambda: kill_ffmpeg(root))
        button_kill_ffmpeg.pack(pady=10)

def kill_ffmpeg(root):
    if isMacOs():
        global g_mac_pid
        os.killpg(os.getpgid(g_mac_pid), signal.SIGTERM)
    elif isWindowsOs():
        global g_windows_pid
        os.kill(g_windows_pid, signal.CTRL_C_EVENT)

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

def inspectVideoFiles(directory, tkinter_window, listbox_completed_videos, index_start, log_file, progress_bar):
    try:
        global g_count
        global g_currently_processing

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
                if filename.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                    if (index_start > count + 1):
                        count += 1
                        continue

                    print(f'PROCESSING: {filename}...')
                    log_file.write(f'PROCESSING: {filename}\n')
                    log_file.flush()

                    global g_progress
                    g_progress.set(calculateProgress(count, totalVideoFiles))
                    tkinter_window.update()

                    g_count.set(f"{count+1} / {totalVideoFiles}")
                    tkinter_window.update()

                    g_currently_processing.set(filename)
                    tkinter_window.update()

                    abs_file_path = os.path.join(root, filename)

                    proc = ''
                    if isMacOs():
                        global g_mac_pid
                        proc = subprocess.Popen(f'./ffmpeg -v error -i {shlex.quote(abs_file_path)} -f null - 2>&1', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        g_mac_pid = proc.pid
                    elif isWindowsOs():
                        global g_windows_pid
                        ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ffmpeg.exe'))
                        proc = subprocess.Popen(f'"{ffmpeg_path}" -v error -i "{abs_file_path}" -f null error.log', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        g_windows_pid = proc.pid
                    else:
                        # Linux not yet supported
                        exit()

                    output, error = proc.communicate()

                    # Debug
                    print(f'output= {output}\n')
                    print(f'error= {error}\n')

                    row_index = count
                    if (index_start != 1):
                        row_index = (count + 1) - index_start

                    ffmpeg_result = ''
                    if isMacOs():
                        ffmpeg_result = output
                    elif isWindowsOs():
                        ffmpeg_result = error

                    row = ''
                    if not ffmpeg_result:
                        # Healthy
                        print("\033[92m{0}\033[00m".format("  HEALTHY -> {}".format(filename)), end='\n')  # red
                        log_file.write(f'  HEALTHY -> {filename}\n')
                        log_file.flush()
                        row = [filename, 0]
                        listbox_completed_videos.insert(tk.END, f' {filename}')
                        listbox_completed_videos.itemconfig(row_index, bg='green')
                        tkinter_window.update()
                    else:
                        # Corrupt
                        print("\033[31m{0}\033[00m".format("  CORRUPTED -> {}".format(filename)), end='\n')  # red
                        log_file.write(f'  CORRUPTED -> {filename}\n')
                        log_file.flush()
                        row = [filename, 1]
                        listbox_completed_videos.insert(tk.END, f' {filename}')
                        listbox_completed_videos.itemconfig(row_index, bg='red')
                        tkinter_window.update()

                    results_file_writer.writerow(row)
                    results_file.flush()

                    count += 1

                    g_progress.set(calculateProgress(count, totalVideoFiles))
                    tkinter_window.update()

        g_count.set("---")
        g_currently_processing.set("N/A")
        progress_bar.stop()
        progress_bar['value'] = 100
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

def start_program(directory, root, index_start, log_file, label_chosen_directory, label_chosen_directory_var, label_video_count, label_video_count_var, label_index_start, entry_index_input, label_explanation, button_start, listbox_completed_videos):
    try:
        label_chosen_directory.destroy()
        label_chosen_directory_var.destroy()
        label_video_count.destroy()
        label_video_count_var.destroy()
        label_index_start.destroy()
        entry_index_input.destroy()
        label_explanation.destroy()
        button_start.destroy()
        listbox_completed_videos.destroy()

        label_progress_text = tk.Label(root, text="Progress:", font=('Helvetica Bold', 18))
        label_progress_text.pack(fill=tk.X, pady=10)

        g_progress.set("0%")
        label_progress_var = tk.Label(root, textvariable=g_progress, font=('Helvetica', 50))
        label_progress_var.pack(fill=tk.X, pady=(0, 10))

        progress_bar = ttk.Progressbar(root, orient="horizontal", mode="indeterminate", length=300)
        progress_bar.pack(pady=(0, 20))
        progress_bar.start()

        label_currently_processing_text = tk.Label(root, text="Currently Processing:", font=('Helvetica Bold', 18))
        label_currently_processing_text.pack(fill=tk.X, pady=10)

        g_count.set("0 / 0")
        label_count_var = tk.Label(root, textvariable=g_count, font=('Helvetica', 16))
        label_count_var.pack(fill=tk.X, pady=(0, 10))

        g_currently_processing.set("N/A")
        label_currently_processing_var = tk.Label(root, textvariable=g_currently_processing, font=('Helvetica', 16))
        label_currently_processing_var.pack(fill=tk.X, pady=(0, 10))

        listbox_completed_videos = tk.Listbox(root, font=('Helvetica', 16))
        listbox_completed_videos.pack(expand=False, fill=tk.BOTH, side=tk.TOP, padx=10, pady=10)
        listbox_completed_videos.bind('<<ListboxSelect>>', lambda e: "break")
        listbox_completed_videos.bind('<Button-1>', lambda e: "break")
        listbox_completed_videos.bind('<Button-2>', lambda e: "break")
        listbox_completed_videos.bind('<Button-3>', lambda e: "break")
        listbox_completed_videos.bind('<ButtonRelease-1>', lambda e: "break")
        listbox_completed_videos.bind('<Double-1>', lambda e: "break")
        listbox_completed_videos.bind('<Double-Button-1>', lambda e: "break")
        listbox_completed_videos.bind('<B1-Motion>', lambda e: "break")

        button_ffmpeg_verify = tk.Button(root, text="ffmpeg Status", width=200, command=lambda: verify_ffmpeg_still_running(root))
        button_ffmpeg_verify.pack(pady=10)

        if isMacOs():
            # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
            button_kill_ffmpeg = MacButton(root, background='#E34234', borderless=1, foreground='white', text="Safely Quit", width=500, command=lambda: kill_ffmpeg_warning(root))
            button_kill_ffmpeg.pack(pady=10)
        elif isWindowsOs():
            button_kill_ffmpeg = tk.Button(root, background='#E34234', foreground='white', text="Safely Quit", width=200, command=lambda: kill_ffmpeg_warning(root))
            button_kill_ffmpeg.pack(pady=10)

        thread = Thread(target=inspectVideoFiles, args=(directory, root, listbox_completed_videos, index_start, log_file, progress_bar))
        thread.start()
    except Exception as e:
        log_file.write(f'ERROR in "start_program": {e}\n\n')
        log_file.flush()

def afterDirectoryChosen(root, directory):
    # Log file
    log_file_path = os.path.join(directory, '_Logs.log')
    log_file_exists = os.path.isfile(log_file_path)
    if log_file_exists:
        os.remove(log_file_path)
    log_file = open(log_file_path, 'a', encoding="utf8")

    totalVideos = countAllVideoFiles(directory)

    label_chosen_directory = tk.Label(root, text="Chosen directory:", font=('Helvetica Bold', 18))
    label_chosen_directory.pack(fill=tk.X, pady=5)
    label_chosen_directory_var = tk.Label(root, wraplength=450, text=f"{directory}", font=('Helvetica', 14))
    label_chosen_directory_var.pack(fill=tk.X, pady=(5, 20))

    label_video_count = tk.Label(root, text="Total number of videos found:", font=('Helvetica Bold', 18))
    label_video_count.pack(fill=tk.X, pady=5)
    label_video_count_var = tk.Label(root, text=f"{totalVideos}", font=('Helvetica', 16))
    label_video_count_var.pack(fill=tk.X, pady=(5, 20))

    listbox_videos_found_with_index = tk.Listbox(root, font=('Helvetica', 16), width=480)
    listbox_videos_found_with_index.pack(padx=10)
    listbox_videos_found_with_index.bind('<<ListboxSelect>>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-2>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-3>', lambda e: "break")
    listbox_videos_found_with_index.bind('<ButtonRelease-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Double-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Double-Button-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<B1-Motion>', lambda e: "break")

    all_videos_found = getAllVideoFiles(directory)
    for video in all_videos_found:
        listbox_videos_found_with_index.insert(tk.END, video)
    root.update()

    label_index_start = tk.Label(root,
                                 text=f"Start at video index (1 - {countAllVideoFiles(directory)}):",
                                 font=('Helvetica Bold', 18))
    label_index_start.pack(fill=tk.X, pady=5)

    entry_index_input = tk.Entry(root, width=50)
    entry_index_input.focus_set()
    entry_index_input.insert(tk.END, '1')
    entry_index_input.pack(fill=tk.X, padx=200)

    label_explanation = tk.Label(root, wraplength=450,
                                 text="The default is '1'. Set index to '1' if you want to start from the beginning and process all videos. If you are resuming a previous operation, then set the index to the desired number. Also note, each run will overwrite the _Logs and _Results files.",
                                 font=('Helvetica Italic', 12))
    label_explanation.pack(fill=tk.X, pady=5, padx=20)

    if totalVideos > 0:
        button_start = tk.Button(root, text="Start Inspecting", width=25, command=lambda: start_program(directory, root, int(entry_index_input.get()), log_file, label_chosen_directory, label_chosen_directory_var, label_video_count, label_video_count_var, label_index_start, entry_index_input, label_explanation, button_start, listbox_videos_found_with_index))
        button_start.pack(pady=20)
    else:
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.resizable(False, False)
        error_window.geometry("400x200")
        error_window.title("Error")

        label_error_msg = tk.Label(error_window, width=375, text="No video files found in selected directory!", font=('Helvetica', 14))
        label_error_msg.pack(fill=tk.X, pady=20)

        button_exit = tk.Button(error_window, text="Exit", width=30, command=lambda: exit())
        button_exit.pack()

# ========================= MAIN ==========================

if isLinuxOs():
    # Linux not yet supported
    exit()

root = tk.Tk()
root.title("Corrupt Video Inspector")
if isMacOs():
    root.geometry("500x650")
if isWindowsOs():
    root.geometry("500x750")
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.ico'))
    root.iconbitmap(default=icon_path)
g_progress = tk.StringVar()
g_count = tk.StringVar()
g_currently_processing = tk.StringVar()
g_mac_pid = ''
g_windows_pid = ''

label_select_directory = tk.Label(root, wraplength=450, justify="left", text="Select a directory to search for all video files within the chosen directory and all of its containing subdirectories", font=('Helvetica', 16))
label_select_directory.pack(fill=tk.X, pady=5, padx=20)

button_select_directory = tk.Button(root, text="Select Directory", width=20, command=lambda: selectDirectory(root, label_select_directory, button_select_directory))
button_select_directory.pack(pady=20)

root.mainloop()