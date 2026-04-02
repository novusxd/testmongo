import json
import os
from pymongo import MongoClient

DB_STORAGE_FILE = "databases.json"

# --- FUNGSI HELPER DATA ---
def load_db_list():
    if not os.path.exists(DB_STORAGE_FILE): return []
    with open(DB_STORAGE_FILE, "r") as f: 
        try: return json.load(f)
        except: return []

def save_db_list(data):
    with open(DB_STORAGE_FILE, "w") as f: 
        json.dump(data, f, indent=4)

# --- CLI MENU ---
def browse_collection(collection):
    # Mengambil semua data ke dalam list untuk navigasi Next/Prev
    cursor = list(collection.find())
    if not cursor:
        print("\n[!] Koleksi ini kosong.")
        input("Tekan Enter untuk kembali...")
        return

    index = 0
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        doc = cursor[index]
        print(f"--- Data {index + 1} dari {len(cursor)} ---")
        print(json.dumps(doc, indent=4, default=str))
        print("\n[N] Next | [P] Prev | [D] Delete | [B] Kembali")
        
        cmd = input(">> ").lower()
        if cmd == 'n' and index < len(cursor) - 1:
            index += 1
        elif cmd == 'p' and index > 0:
            index -= 1
        elif cmd == 'd':
            confirm = input("Yakin hapus dokumen ini dari MongoDB? (y/n): ")
            if confirm == 'y':
                collection.delete_one({"_id": doc["_id"]})
                cursor.pop(index)
                print("Terhapus!")
                if not cursor: break
                if index >= len(cursor): index -= 1
        elif cmd == 'b':
            break

def cli_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MONGO MANAGER (SIMPLE VERSION) ===")
        print("1. Masukkan Mongo URL Baru")
        print("2. Lihat Database Tersimpan")
        print("3. Hapus Database dari List")
        print("4. Keluar")
        
        pilihan = input("Pilih menu: ")

        if pilihan == '1':
            url = input("Masukkan Mongo URL: ").strip()
            if url:
                dbs = load_db_list()
                if url not in dbs:
                    dbs.append(url)
                    save_db_list(dbs)
                    print("URL Berhasil disimpan ke list.")
                else:
                    print("URL sudah ada di dalam list.")
            input("\nTekan Enter...")

        elif pilihan == '2':
            dbs = load_db_list()
            if not dbs:
                input("List kosong. Masukkan URL terlebih dahulu. (Enter)")
                continue
            
            print("\n--- Pilih Database URL ---")
            for i, url in enumerate(dbs, 1):
                print(f"{i}. {url[:70]}...")
            
            try:
                idx = int(input("\nPilih nomor URL: ")) - 1
                if idx < 0 or idx >= len(dbs): raise ValueError
                
                client = MongoClient(dbs[idx], serverSelectionTimeoutMS=5000)
                # Tes koneksi
                client.admin.command('ping')
                
                # Memilih Database
                db_names = [n for n in client.list_database_names() if n not in ['admin', 'local', 'config']]
                print("\n--- Daftar Database ---")
                for i, n in enumerate(db_names, 1): print(f"{i}. {n}")
                db_sel = client[db_names[int(input("Pilih Nomor DB: "))-1]]
                
                # Memilih Koleksi
                col_names = db_sel.list_collection_names()
                print("\n--- Daftar Koleksi (Folder) ---")
                for i, n in enumerate(col_names, 1): print(f"{i}. {n}")
                col_sel = db_sel[col_names[int(input("Pilih Nomor Koleksi: "))-1]]
                
                browse_collection(col_sel)
            except Exception as e:
                print(f"\n[!] Error: {e}")
                input("Tekan Enter...")

        elif pilihan == '3':
            dbs = load_db_list()
            if not dbs:
                input("List kosong. (Enter)")
                continue
                
            for i, url in enumerate(dbs, 1):
                print(f"{i}. {url[:70]}...")
            
            try:
                idx = int(input("\nNomor URL yang akan dihapus dari LIST: ")) - 1
                removed = dbs.pop(idx)
                save_db_list(dbs)
                print(f"Berhasil menghapus URL dari list lokal.")
            except:
                print("Gagal menghapus.")
            input("\nTekan Enter...")

        elif pilihan == '4':
            print("Keluar...")
            break

if __name__ == "__main__":
    try:
        cli_menu()
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
