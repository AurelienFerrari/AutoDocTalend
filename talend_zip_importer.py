import os
import zipfile
import shutil

# Directories can be changed if needed
ZIPS_DIR = 'zips'  # Folder where you put ZIP files to process
DOCUMENTATIONS_DIR = 'documentations'  # Where to place .html_0.1.item files
ARCHIVES_DIR = 'archives'  # Where to archive processed ZIP files

os.makedirs(DOCUMENTATIONS_DIR, exist_ok=True)
os.makedirs(ARCHIVES_DIR, exist_ok=True)

zip_files = [f for f in os.listdir(ZIPS_DIR) if f.lower().endswith('.zip')]
if not zip_files:
    print(f"Aucun fichier zip trouvé dans {ZIPS_DIR}")
for filename in zip_files:
    zip_path = os.path.join(ZIPS_DIR, filename)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        temp_extract_dir = os.path.join(ZIPS_DIR, '__extract_temp__')
        zip_ref.extractall(temp_extract_dir)
        # Cherche le premier fichier .html dans le zip
        found = False
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                if file.lower().endswith('.html'):
                    src = os.path.join(root, file)
                    dst = os.path.join(DOCUMENTATIONS_DIR, file)
                    shutil.copy2(src, dst)
                    print(f"Copié {file} dans {DOCUMENTATIONS_DIR}")
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"Aucun fichier .html trouvé dans {filename}")
        shutil.rmtree(temp_extract_dir)
    # Déplace le zip dans archives
    shutil.move(zip_path, os.path.join(ARCHIVES_DIR, filename))
    print(f"Archivé {filename} dans {ARCHIVES_DIR}")
