import json
import os
import requests
from pymongo import MongoClient
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load konfigurasi dari .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Client("mongo_manager", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
DB_STORAGE_FILE = "databases.json"

def load_db_list():
    if not os.path.exists(DB_STORAGE_FILE): return []
    with open(DB_STORAGE_FILE, "r") as f: return json.load(f)

def save_db_list(data):
    with open(DB_STORAGE_FILE, "w") as f: json.dump(data, f, indent=4)

def send_log(msg):
    try:
        with app:
            app.send_message(ADMIN_ID, f"🔔 **Update Database:**\n{msg}")
    except: pass

def browse_collection(collection):
    cursor = list(collection.find())
    if not cursor:
        print("\n[!] Koleksi ini kosong.")
        input("Tekan Enter untuk kembali...")
        return

    index = 0
    seen_indices = set() # Untuk melacak apa yang sudah dilihat jika diperlukan

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        doc = cursor[index]
        seen_indices.add(index)
        
        print(f"--- Data {index + 1} dari {len(cursor)} ---")
        print(json.dumps(doc, indent=4, default=str))
        print("\n[N] Next | [P] Prev | [D] Delete | [B] Kembali")
        
        cmd = input(">> ").lower()
        if cmd == 'n' and index < len(cursor) - 1:
            index += 1
        elif cmd == 'p' and index > 0:
            index -= 1
        elif cmd == 'd':
            confirm = input("Hapus data ini? (y/n): ")
            if confirm == 'y':
                collection.delete_one({"_id": doc["_id"]})
                cursor.pop(index)
                if not cursor: break
                if index >= len(cursor): index -= 1
        elif cmd == 'b':
            break

def main():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MONGO URL MANAGER ===")
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
                    send_log(f"URL Baru ditambahkan:\n`{url}`")
                    print("Berhasil disimpan.")
                else:
                    print("URL sudah ada di list.")
            input("\nTekan Enter...")

        elif pilihan == '2':
            dbs = load_db_list()
            if not dbs:
                print("List kosong.")
                input("\nTekan Enter...")
                continue
            
            for i, url in enumerate(dbs, 1):
                print(f"{i}. {url[:50]}...")
            
            idx = int(input("Pilih nomor URL: ")) - 1
            client = MongoClient(dbs[idx])
            
            # Pilih DB & Koleksi
            db_names = client.list_database_names()
            for i, n in enumerate(db_names, 1): print(f"{i}. {n}")
            db_sel = client[db_names[int(input("Pilih DB: "))-1]]
            
            col_names = db_sel.list_collection_names()
            for i, n in enumerate(col_names, 1): print(f"{i}. {n}")
            col_sel = db_sel[col_names[int(input("Pilih Koleksi: "))-1]]
            
            browse_collection(col_sel)

        elif pilihan == '3':
            dbs = load_db_list()
            for i, url in enumerate(dbs, 1): print(f"{i}. {url[:50]}...")
            idx = int(input("Nomor yang akan dihapus: ")) - 1
            removed = dbs.pop(idx)
            save_db_list(dbs)
            send_log(f"URL Dihapus:\n`{removed}`")
            print("Berhasil dihapus.")
            input("\nTekan Enter...")

        elif pilihan == '4':
            break

# Handler untuk bot (dipisahkan atau dijalankan via thread jika ingin simultan)
# Untuk kesederhanaan, perintah /dblist bisa dicek via skrip terpisah atau integrasi polling
if __name__ == "__main__":
    main()
