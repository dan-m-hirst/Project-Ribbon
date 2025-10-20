
from webbrowser import get, open, register, BackgroundBrowser
from sys import argv

def launch_localhost(chrome_path):
    register('chrome',None,BackgroundBrowser(chrome_path))
    get('chrome').open("http://localhost:8050/")