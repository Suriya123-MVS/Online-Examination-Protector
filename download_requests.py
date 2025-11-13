import requests
import os

os.makedirs('models', exist_ok=True)

url = 'https://pjreddie.com/media/files/yolov3.weights'
filename = 'models/yolov3.weights'

print("Downloading YOLOv3 weights...")

try:
    # Use a session with headers to mimic a browser
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    response = session.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded = 0
    
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            file.write(data)
            if total_size > 0:
                percent = (downloaded * 100) // total_size
                print(f'\rDownload progress: {percent}% ({downloaded}/{total_size} bytes)', end='', flush=True)
    
    print(f"\nDownload completed! File size: {downloaded} bytes")
    
except Exception as e:
    print(f"\nError downloading: {e}")