from __future__ import unicode_literals

import os, sys, ssl, pathlib, time
from threading import Thread, Semaphore

import youtube_dl
from datetime import datetime
from pytube import YouTube
from tqdm.auto import tqdm

def start():
    inputOption = input("Escolha uma forma de input:\n[1] via terminal\n[2] via arquivo\nOption: ")
    if inputOption != "1" and inputOption != "2":
        start()
        return

    if inputOption == "1":
        runTerminalAction()
    else:
        runFileAction()

def runTerminalAction():
    opc = input("[1] youtube\n[2] vimeo\nOption: ")
    if opc != "1" and opc != "2":
        start()
        return
    
    if opc == "2":       
        link = input("Cole aqui o link do vídeo:\n")
        download_vimeo_video(link, shell=True)

    if opc == "1":
        if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
                getattr(ssl, '_create_unverified_context', None)):
            ssl._create_default_https_context = ssl._create_unverified_context
        link = input("Cole aqui o link do vídeo:\n")
        download_yt_video(link, shell=True)


def runFileAction():
    path = pathlib.Path().absolute()
    print("Use o arquivo de leitura 'input.txt' que está em %s." % path)
    print("  - Estruture o arquivo de leitura da seguinte forma:")
    print("  - <youtube-or-vimeo>,<video-link>,<file-name_optional>")
    print("  - Ex: youtube,https://www.youtube.com/watch?videoexample")
    start = input("Tudo proto? (s): ")
    if (start != "s"): return
    
    print()
    open("output.txt", "w")
    threadsGroup = []
    Semaphore(value=10)

    for line in open("input.txt", 'r'):
        columns = line.split(",")
        if columns[0] != "youtube" and columns[0] != "vimeo": 
            print("Invalid format")
            break
        link = columns[1]
        name = None
        if len(columns) > 2 and columns[2] and columns[2] != "":
            name = columns[2]
        args = [link, name]

        if "youtube":
            create_thread(threadsGroup, download_yt_video, args)
        else:
            create_thread(threadsGroup, download_vimeo_video, args)
    
    for t in threadsGroup:
        t.join()

    time.sleep(1)
    print("\nFINISHED: Verifique o arquivo de saída 'output.txt' que está em %s.\n" % path)

def create_thread(threadsGroup, threaded_function, args=()):
    thread = Thread(target = threaded_function, args=args)
    thread.start()
    threadsGroup.append(thread)

def download_yt_video(link, name=None, shell=False):
    progressbar = ProgressBar(shell, name)
    yt = YouTube(link, on_progress_callback=progressbar.on_progress, on_complete_callback=progressbar.on_complete)
    yt.streams.filter(progressive=True, file_extension='mp4') \
        .order_by('resolution') \
        .desc() \
        .first() \
        .download(output_path=("videos_{}").format(datetime.today().strftime('%Y-%m-%d-%H-%M')), filename=name)
        
def download_vimeo_video(link, name=None, shell=False):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
        
    print("Video foi baixado. \nEstá na pasta {}".format( os.getcwd() ))

class ProgressBar:

    def __init__(self, shell=False, filename=None):
        self.shell = shell
        self.filename = filename
        self.pbar = False
        self.lastupdate = 0
        self.output = open("output.txt", "a")

    def on_progress(self, stream, file_handle, bytes_remaining):
        if (not self.pbar):
            self.filename = self.filename.rstrip() if self.filename else stream.title
            self.pbar = tqdm(desc=self.filename, total=bytes_remaining, ncols=150, leave=False)
            self.lastupdate = bytes_remaining
            
        self.pbar.update(self.lastupdate - bytes_remaining)
        self.lastupdate = bytes_remaining
       
    def on_complete(self, stream, filepath):
        if self.pbar:
            self.pbar.close()
            self.pbar.write("Video '%s' baixado." % self.filename)

        if (self.shell):
            print("Video '%s' baixado." % self.filename)
        else:
            self.output.write("{}; {}\n".format(self.filename, filepath))

if __name__ == "__main__":
    start()
