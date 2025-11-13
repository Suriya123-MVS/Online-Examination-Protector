import urllib.request
import os
import ssl

# Bypass SSL verification (in case of certificate issues)
ssl._create_default_https_context = ssl._create_unverified_context

# Create models directory
os.makedirs('models', exist_ok=True)

url = 'https://pjreddie.com/media/files/yolov3.weights'
filename = 'models/yolov3.weights'

print("Downloading YOLOv3 weights (237 MB)...")
print("This may take several minutes depending on your internet connection...")

def download_with_progress(url, filename):
    def progress_callback(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, (downloaded * 100) // total_size)
        print(f"\rDownload progress: {percent}% ({downloaded}/{total_size} bytes)", end='', flush=True)
    
    urllib.request.urlretrieve(url, filename, progress_callback)
    print("\nDownload completed!")

download_with_progress(url, filename)

# Verify file size
file_size = os.path.getsize(filename)
expected_size = 248007048  # Correct file size in bytes
print(f"Downloaded file size: {file_size} bytes")
print(f"Expected file size: {expected_size} bytes")

if file_size == expected_size:
    print("✓ File size matches expected size - download successful!")
else:
    print("✗ File size doesn't match - download may be corrupted")