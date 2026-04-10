import os
import sys
from rembg import remove
from PIL import Image
import glob

def process_file(input_path, output_path):
    print(f"[*] Processing: {os.path.basename(input_path)}...")
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
            output_data = remove(input_data)
            with open(output_path, 'wb') as o:
                o.write(output_data)
        print(f"[+] Success! Saved to: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"[!] Error processing {input_path}: {e}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "output")

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 查找 input 文件夹中的所有图片
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(input_dir, ext)))

    if not files:
        print("[-] No images found in 'input/' folder.")
        print("    Please put your images in the 'input' directory and run again.")
        return

    print(f"[*] Found {len(files)} images. Starting AI removal...")
    
    for f in files:
        filename = os.path.basename(f)
        # 统一输出为透明 PNG
        out_name = os.path.splitext(filename)[0] + ".png"
        out_path = os.path.join(output_dir, out_name)
        process_file(f, out_path)

    print("\n[✔] All tasks finished!")

if __name__ == "__main__":
    main()
