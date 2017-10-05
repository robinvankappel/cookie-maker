### Basics, db-filler and watcher ###
download and install git bash @https://www.google.nl/url?sa=t&rct=j&q=&esrc=s&source=web&cd=2&cad=rja&uact=8&ved=0ahUKEwjysMPeobbSAhWRDRoKHSFlBVwQFggoMAE&url=https%3A%2F%2Fgit-scm.com%2Fdownload%2Fwin&usg=AFQjCNGgkEevr3G3s0qGAw9_URQwLcb5CQ&sig2=UZOYlsE6HGILM5exJ6FdvQ

git clone https://robinvankappel@bitbucket.org/cookiemonstershq/installers.git
git clone https://robinvankappel@bitbucket.org/cookiemonstershq/db-filler.git
git clone https://robinvankappel@bitbucket.org/cookiemonstershq/watcher.git
download and install Chrome
download and install python @https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi
download and install PyCharm @https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=windows

add python path to environment variable 'Path'

install pip (via pycharm)
cmd: cd to C:\Python27\Scripts: 'pip install -r D:\db-filler\requirements.txt'
run D:\db-filler\MakeOutputfolders.bat


#### Solving
check paths in config_paths.py
start runWatchers.bat in D:\watcher
start johan-app.py (PyCharm or only file)

_________
tips and tricks:
-if program returns 'pftables.dat is missing' then this file cannot be found in the current working directory. The batch file which calls this function should be run as administrator. Therefore disable UAC (User Account Control of Windows); restart is required.