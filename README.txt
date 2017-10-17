### Basics, cookie_maker and cookie_sender ###
download and install git bash @https://www.google.nl/url?sa=t&rct=j&q=&esrc=s&source=web&cd=2&cad=rja&uact=8&ved=0ahUKEwjysMPeobbSAhWRDRoKHSFlBVwQFggoMAE&url=https%3A%2F%2Fgit-scm.com%2Fdownload%2Fwin&usg=AFQjCNGgkEevr3G3s0qGAw9_URQwLcb5CQ&sig2=UZOYlsE6HGILM5exJ6FdvQ

git clone https://robinvankappel@bitbucket.org/cookiemonstershq/cookie.git
download and install Chrome
download and install python @https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi
download and install PyCharm @https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=windows

add python path to environment variable 'Path'

install pip (via pycharm)
cmd: cd to C:\Python27\Scripts: 'pip install -r D:\cookie\requirements.txt'

#### Solving
check general settings in config_cookie.py
start cookie_sender/cookie_sender.pyc
start cookie_maker/cookie_maker.pyc

_________
tips and tricks:
-if program returns 'pftables.dat is missing' then this file cannot be found in the current working directory. The batch file which calls this function should be run as administrator. Therefore disable UAC (User Account Control of Windows); restart is required.