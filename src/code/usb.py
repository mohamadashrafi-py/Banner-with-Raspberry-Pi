import os
import shutil
from video import create_video

user = os.getlogin()


def get_drives():
    drives = []
    mount_points = [f'/media/{user}', '/mnt', '/media']
    for mp in mount_points:
        if os.path.exists(mp):
            for entry in os.listdir(mp):
                full_path = os.path.join(mp, entry)
                if os.path.ismount(full_path):
                    drives.append(full_path + '/')
    return drives

def setup():
    drive = get_drives()
    image_format = ['.png', '.jpg', '.jpeg']
    required_images = range(1, 5)
    
    if os.path.exists(os.path.join(drive[0], 'video.mp4')):
        src = os.path.join(drive[0], 'video.mp4')
        dst = os.path.join('/home', user, 'Project', 'video.mp4')
        shutil.copy(src, dst)
        create_video()
        
    for image in required_images:
        for available_format in image_format:
            if os.path.exists(os.path.join(drive[0], (str(image) + available_format))):
                src = os.path.join(drive[0], (str(image) + available_format))
                dst = os.path.join('/home', user, 'Project', (str(image) + available_format))
                shutil.copy(src, dst)
    
