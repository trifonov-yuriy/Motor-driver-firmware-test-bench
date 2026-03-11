import subprocess
import sys

def upload_hex(port, hex_file):
    try:
        subprocess.run([
            'avrdude',
            '-p', 'atmega328p',
            '-c', 'arduino',
            '-P', port,
            '-b', '115200',
            '-U', f'flash:w:{hex_file}:i'
        ], check=True)
        print("Upload successful!")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    upload_hex('COM15', 'avr-project.hex')