import os

def read_files_with_directory_headers(directory, extensions):
    print(f"Dizin: {directory}")
    """
    Belirtilen dizindeki dosyaları okur ve dizin bilgisi ile birlikte içeriklerini birleştirir.
    
    :param directory: Taranacak dizin.
    :param extensions: Dosya uzantıları listesi.
    :return: İçeriği tek bir metin olarak döner.
    """
    all_content = f"Dizin: {directory}\n\n"
    
    for root, dirs, files in os.walk(directory):
        # venv klasörünü atla
        if 'venv' in dirs:
            dirs.remove('venv')
            
        for file in files:
            # get-pip.py ve belirtilen uzantılara sahip olmayan dosyaları atla
            if file == 'get-pip.py' or not file.endswith(tuple(extensions)):
                continue
                
            file_path = os.path.join(root, file)
            try:
                # Başlık olarak dosya yolu ekle
                all_content += f"==== Dosya: {file_path} ====\n"
                
                # Dosya içeriğini oku
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_content += f.read() + "\n\n"
            except Exception as e:
                print(f"Dosya okunurken hata oluştu: {file_path}, Hata: {e}")
    
    return all_content


# Kullanım
directory_to_scan = r"C:\Users\Tuga-Munir\source\repos\chatbot_framework"  # Tarayacağınız dizin
file_extensions = ["py", "html", "css", "js"]  # Uzantılar

# Tüm dosyaların içeriğini oku
content = read_files_with_directory_headers(directory_to_scan, file_extensions)

# İçeriği aynı dizine kaydet
output_file = os.path.join(directory_to_scan, "merged_content_with_headers.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Tüm dosyaların içeriği başlıklarla birlikte '{output_file}' dosyasına yazıldı.")
