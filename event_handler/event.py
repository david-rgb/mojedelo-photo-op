import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import os
from datetime import datetime
import mysql.connector
from configparser import ConfigParser
from ftplib import FTP, error_perm
import json

ftp = FTP('ftp.klemenstudios.at')
ftp.login(user='david@klemenstudios.at', passwd='Moje$Delo#2023!')

def save_to_database(file_name,user_id,current_date):
    endpoint = "https://mojedelo.scripter.si/api/img"
    payload = json.dumps({"USER_ID": user_id,"IMG_URL":f"https://mojedelo.scripter.si/static/{current_date}/{file_name}"})
    headers = {"Content-Type": "application/json"}
    r = requests.post(endpoint,data=payload,headers=headers)
    print("Request returned status code: ", r.status_code)

def folder_exists(ftp, folder_name):
    try:
        ftp.cwd(folder_name)
        return True
    except error_perm:
        return False

def upload_file(ftp, target_folder, remote_folder, file_name):
    filepath = os.path.join(target_folder, file_name)
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as file:
            ftp.storbinary(f'STOR {remote_folder}/{file_name}', file)
    else:
        print(f"The file '{file_name}' does not exist in the target folder.")

config = ConfigParser()
config.read('api.cfg')

# Configure database connection
db_config = {
    "host": config.get('database', 'host'),
    "user": config.get('database', 'user'),
    "password": config.get('database', 'password'),
    "database": config.get('database', 'database')
}

screen_width = None
screen_height = None

# Function to get database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

class Watcher:
    DIRECTORY_TO_WATCH = input("Please enter the path to the folder: ")
    FILE_EXTENSION = input("Please enter file extension for images (.jpg, .png): ")

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Observer stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None
        else:
            response = requests.get('https://mojedelo.scripter.si/api/user')
            if response.status_code == 200:
                user_id = response.json()[0]['USER_ID']
                current_time = datetime.now().strftime('%H%M%S')
                new_file_name = f"{user_id}_{current_time}{os.path.splitext(event.src_path)[1]}{Watcher.FILE_EXTENSION}"
                os.rename(event.src_path, os.path.join(os.path.dirname(event.src_path), new_file_name))
                print(f"File renamed to: {new_file_name}")
                current_date = datetime.now().strftime('%Y-%m-%d')
                if not folder_exists(ftp,current_date):
                    ftp.mkd(current_date)
                upload_file(ftp,Watcher.DIRECTORY_TO_WATCH,f"/mojedelo/static/{current_date}",new_file_name)
                save_to_database(new_file_name,user_id,current_date)
            else:
                print("Failed to retrieve USER_ID from API")

if __name__ == '__main__':
    w = Watcher()
    w.run()