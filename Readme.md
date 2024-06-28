
# Corrupt Video Inspector


<p align="right">
  <img src="icon.png" width="75" height="75" />
</p>

### About
Occasionally you come across a video file that is corrupt. Whent trying to play the file in a desktop video player, it is not able to be viewed at all. Other times, it is not as black and white as a video file being "playable" or "non-playable". Sometimes videos have pixilated/glitchy/buggy/fuzzy/freezy sections within several timestamps of the video. For example, the first hour of the video will run smoothly, but then every few minutes there will be a 20 second chunk of pixilated glitchiness, only to resume normally once that bad sector has passed. So it may be still watchable, but annoying and detracts from the overall enjoyment of the movie. If you are a movie collector like me, you have thousands of files and a small fraction of them may be lightly-corrupt. The goal was to identify which files in my collection were corrupt. This program is made for the sophisticated schemer. 

### Functionality
This program searches though a selected directory and its subdirectories for all video file types. The file types are analyzed under the hood using `ffmpeg`. If any bad sectors in the video file are found, it will be marked as corrupt. If not, it is deemed a healthy file. This performs a very thorough scan of each file and is the best way to most accurately assess the integrity of the video files. The program is written in Python and has a GUI interface built with `tkinter`. This program was built with macOS and Apple-silicone in mind. `py2app` was used to create a standalone application that runs on macOS without further configuration. 

*Update: A Windows executable has now been created using `pyinstaller`*

### How to Use
* If using macOS, download and run the latest `Corrupt Video Inspector.dmg` file found in the macOS [builds](https://github.com/nhershy/CorruptVideoFileInspector/tree/main/builds/macOS/v5) folder.
* If using Windows, download and run the latest `CorruptVideoInspector.exe` file found in the WindowsOS [builds](https://github.com/nhershy/CorruptVideoFileInspector/tree/main/builds/WindowsOS) folder. *Note: When first running the application on Windows OS, Windows Defender will display a warning message since this application is unsigned and not recognized by your PC. Click "More Info -> Run Anyway". I assure you this application is safe, as you can inspect the code yourself above.*
* Linux is not yet supported.
* Chose a directory (this will search the selected directory and all containing subdirectories for all video files)
* Choose an index to start the scan at **(leave '1' for default to start from the beginning and scan all files)**. This "index" option allows you resume scanning from a certain video. For example, if your computer accidently restarted after scanning 90 of 100 videos in a directory, you can restart the program and type "90" to start from the 90th video file instead of scanning all videos over from the beginning. If you are unsure which video was being scanned when the computer restarted, check the "_Results.csv" file for an indexed listing of all files that have successfully been scanned/completed. 
* The scan will automatically start once an index is chosen. You will be prompted with a window showing the total completed progress (0-100%), the file that is currently being scanned, and a list of all previously scanned videos which are marked with a green/red highlight, indicating healthy/corrupt. In addition to the GUI, two files are automatically created upon running the application: _Logs.txt and _Results.csv. These files are created and stored in the directory that was first chosen to scan for video files. These files will be overwritten on each run of the program. So remember to move them to another directory to store long-term once a full directory scan has been completed. _Logs.txt simply shows a text-based record of each file scanned, if it is healthy/corrupt, and any exceptions encountered during the scan. _Results.csv shows two colummns: "Video File" and "Corrupt". The "Corrupt" column will have a "1" if the file is corrupt. Otherwise, a "0" indicates the file is healthy. 

#### macOS 
<p align="center">
  <img src="assets/demo-mac.jpg" />
</p>

#### Windows OS
<p align="center">
  <img src="assets/demo-windows.png" />
</p>

### Technical references
* [FFMPEG official documentation](https://ffmpeg.org/ffmpeg.html)
* [The command to scan a video file for integrity](https://gist.github.com/ridvanaltun/8880ab207e5edc92a58608d466095dec)
* [More details on checking integrity of video files](https://superuser.com/questions/100288/how-can-i-check-the-integrity-of-a-video-file-avi-mpeg-mp4)
* [tkinter](https://docs.python.org/3/library/tkinter.html)
* [py2app](https://py2app.readthedocs.io/en/latest/#)
* [pyinstaller](https://pyinstaller.org/en/stable/)

### Caveats
* Where the human eye does not detect any pixelation or glitches within a video file, that does not guarantee that the file fully lacks corrupt frames found by `ffmpeg`. If <em>any</em> bad frames are found in the video file, it is still marked “corrupt”. Maybe a future update to the program could allow the user to specify a certain threshold or “percent of corruption”. E.g. The user sets a tolerance of 2% corruptness. So if 2% or less of the file has bad frames, then that video could still be marked healthy. However, this is a slippery slope. Because even in that 2% threshold could the video contain pixelation to the human eye when watching it... But ideally, the video file should not contain any bad frames, regardless of if pixilation is noticed by the watcher or not. If there are corrupt frames at all, this should signal to the user to check why: is it an incomplete download? Is the program rendering the vides at fault? Etc.
* Since this utilizes an extremely thorough scan technique, the process is very slow. A 2GB movie may take about 2-5 minutes to scan. A 50GB movie may take 10-20 minutes to scan. If your collection is big, the scanning process can take days. This is all dependent on your hardware, of course. But since `ffmpeg` utilizes an in-depth scan, every sector of the video is scanned, so there are no false positives/negatives. Other scanning techniques may scan the video quickly, but in reality only the metadata is scanned, not the file itself. There are also other scanning techniques that will scan the first 5% of the video and if no error is found, it will be marked healthy. But this is not accurate either because the video may have unhealthy sections within the last 10% of the movie. Therefore, this technique is the most accurate, forfeiting speed for precision. 
* `ffmpeg` will fully utilize the computer's CPU (80-100%)
* If the main GUI application is prematurely closed before all the selected files have been scanned, the `ffmpeg` process will continue run in the background. This will continue to drain the CPU of the machine. This happens becaue the main program calls `ffmpeg` as a subprocess and that subprocess is running on the host machine independently of the Corrupt Video Inspector shell. Thus, if the main application is prematurely closed, you must manually terminate the `ffmpeg` process on the host computer. In macOS, open Activity Monitor, search for `ffmpeg`, and kill the process. In Windows, open Task Manager, search for `ffmpeg`, and kill the process. In both cases, in order to find the process easily, you can order by CPU percentage and `ffmpeg` should be the process consuming the most cpu on the machine. 

*For tkinter to work on Mac M1, must use python 3.10.5 or greater
