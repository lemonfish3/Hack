import os
import subprocess

def create_icon():
    # Create icons directory if it doesn't exist
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    # Source PNG file
    png_path = os.path.join(os.path.dirname(__file__), 'images.png')
    
    # Create icon.iconset directory
    iconset_dir = os.path.join(os.path.dirname(__file__), 'icon.iconset')
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)
    
    # Generate different icon sizes
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in sizes:
        # Generate normal size
        output_path = os.path.join(iconset_dir, f'icon_{size}x{size}.png')
        subprocess.run(['sips', '-z', str(size), str(size), png_path, '--out', output_path])
        
        # Generate @2x size
        if size * 2 <= 1024:
            output_path = os.path.join(iconset_dir, f'icon_{size}x{size}@2x.png')
            subprocess.run(['sips', '-z', str(size*2), str(size*2), png_path, '--out', output_path])
    
    # Convert iconset to icns
    icns_path = os.path.join(os.path.dirname(__file__), 'icon.icns')
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path])
    
    # Clean up iconset directory
    subprocess.run(['rm', '-rf', iconset_dir])
    
    print(f"Icon created and saved at: {icns_path}")

if __name__ == '__main__':
    create_icon() 