import subprocess
import json

def create_video():
    input_file = '/home/mohamad/Project/video.mp4' 
    output_file = '/home/mohamad/Project/main_video.mp4'

    command_duration = ['ffprobe', '-v' , 'error', '-show_entries', 'format=duration', '-of', 'json', input_file]

    try:
        duration_result = subprocess.run(command_duration, check=True, stdout=subprocess.PIPE, text=True)
        duration = int(json.loads(duration_result.stdout)['format']['duration'].split('.')[0])
        
        if duration <= 20:
            creation_time = 50
        
        elif duration <= 30:
            creation_time = 45
        
        elif duration <= 40:
            creation_time = 40
        
        elif duration <= 50:
            creation_time = 35
        
        elif duration <= 60:
            creation_time = 30
            
        else:
            creation_time = 25
            
        command_creation = ['ffmpeg', '-stream_loop', str(creation_time), '-i', input_file, '-c', 'copy', '-y', output_file]
        subprocess.run(command_creation)

    except:
        pass
