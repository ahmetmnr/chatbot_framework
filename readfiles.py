import os

# === SETTINGS (Customize as needed) / AYARLAR (İsteğinize göre düzenleyin) ===

# Directory to scan / Tarayacağınız dizin
DIRECTORY_TO_SCAN = r"C:\Users\Tuga-Munir\source\repos\chatbot_framework"

# Folders to exclude / Hariç tutmak istediğiniz klasörler
IGNORED_DIRS = ["venv", ".git", "__pycache__"]

# Files to exclude / Hariç tutmak istediğiniz dosyalar
IGNORED_FILES = ["get-pip.py", ".gitignore"]

# Only files with these extensions will be read / Sadece bu uzantılara sahip dosyalar okunacak
FILE_EXTENSIONS = ["py", "html", "css", "js"]

# Full file path for saving the output / Çıktının kaydedileceği tam dosya yolu
OUTPUT_FILE = os.path.join(DIRECTORY_TO_SCAN, "merged_content_with_headers.txt")


def get_directory_tree(directory: str, prefix: str = "", ignored_dirs: list[str] = None) -> str:
    """
    Creates a tree structure of directories and files
    Dizin ve dosyaların ağaç yapısını oluşturur
    """
    if ignored_dirs is None:
        ignored_dirs = []
        
    tree = ""
    entries = os.listdir(directory)
    entries = [e for e in entries if e not in ignored_dirs]
    entries.sort()
    
    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = i == len(entries) - 1
        
        if os.path.isdir(path):
            tree += f"{prefix}{'└──' if is_last else '├──'} {entry}/\n"
            extension = "    " if is_last else "│   "
            tree += get_directory_tree(path, prefix + extension, ignored_dirs)
        else:
            tree += f"{prefix}{'└──' if is_last else '├──'} {entry}\n"
            
    return tree


def read_files_with_directory_headers(
    directory: str,
    extensions: list[str],
    ignored_dirs: list[str] = None,
    ignored_files: list[str] = None
) -> str:
    """
    Reads files in the specified directory and merges their content with directory information.
    Belirtilen dizindeki dosyaları okur ve dizin bilgisi ile birlikte içeriklerini birleştirir.

    :param directory: Directory to scan / Taranacak dizin.
    :param extensions: List of file extensions (e.g., ["py", "js"]) / Dosya uzantıları listesi (örn. ["py", "js"]).
    :param ignored_dirs: List of folders to exclude from scanning / Taranması istenmeyen klasörlerin listesi.
    :param ignored_files: List of files to completely ignore / Dosya adından tamamen kaçınılacak dosyaların listesi.
    :return: Returns the content as a single text / İçeriği tek bir metin olarak döndürür.
    """
    if ignored_dirs is None:
        ignored_dirs = []
    if ignored_files is None:
        ignored_files = []

    # First add directory tree / Önce dizin ağacını ekle
    all_content = "Directory Tree / Dizin Ağacı:\n"
    all_content += "========================\n"
    all_content += get_directory_tree(directory, ignored_dirs=ignored_dirs)
    all_content += "\n\nFile Contents / Dosya İçerikleri:\n"
    all_content += "========================\n\n"
    all_content += f"Directory: {directory}\n\n"

    for root, dirs, files in os.walk(directory):
        # Remove folders to be excluded / Hariç tutulması istenen klasörleri çıkar
        for d in ignored_dirs:
            if d in dirs:
                dirs.remove(d)

        for file in files:
            # Skip excluded files or files not in the extension list / Hariç tutulan dosyaları veya uzantı listesinde olmayanları atla
            if file in ignored_files or not file.endswith(tuple(extensions)):
                continue

            file_path = os.path.join(root, file)
            try:
                # File header / Dosya başlığı
                all_content += f"==== File: {file_path} ====\n"

                # Read file content / Dosya içeriğini oku
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_content += f.read() + "\n\n"
            except Exception as e:
                print(f"Error reading file: {file_path}\nError: {e}\n")  # Error message / Hata mesajı

    return all_content


if __name__ == "__main__":
    # Read the content of all files / Tüm dosyaların içeriğini oku
    merged_content = read_files_with_directory_headers(
        DIRECTORY_TO_SCAN,
        FILE_EXTENSIONS,
        IGNORED_DIRS,
        IGNORED_FILES
    )

    # Save the content to the specified file / İçeriği belirlenen dosyaya kaydet
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(merged_content)

    print(f"The content of all files with headers has been written to '{OUTPUT_FILE}'.")  # Success message / Başarı mesajı
