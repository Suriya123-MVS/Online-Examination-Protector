import requests
import os

os.makedirs('models', exist_ok=True)

# Try multiple alternative sources
sources = [
    'https://github.com/pjreddie/darknet/releases/download/yolov3/yolov3.weights',
    'https://drive.google.com/uc?export=download&id=1L-SO7fQo9by66mS-_6o4qD9UveM2h-cR',
    'https://www.dropbox.com/s/6a0436qfwc0q5qo/yolov3.weights?dl=1'
]

filename = 'models/yolov3.weights'

for i, url in enumerate(sources):
    print(f"Trying source {i+1}/{len(sources)}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded * 100) // total_size
                        print(f'\rProgress: {percent}%', end='', flush=True)
        
        file_size = os.path.getsize(filename)
        if file_size > 200000000:  # Should be > 200MB
            print(f"\n✓ Success! Downloaded {file_size} bytes from source {i+1}")
            break
        else:
            print(f"\n✗ File too small ({file_size} bytes), trying next source...")
            os.remove(filename)
            
    except Exception as e:
        print(f"\n✗ Failed with source {i+1}: {e}")
        continue
else:
    print("All download sources failed.")