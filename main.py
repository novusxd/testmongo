import json
import os
import threading
import asyncio
from pymongo import MongoClient
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load konfigurasi dari .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Inisialisasi Bot
app = Client("mongo_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
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

def send_bot_log(msg):
    """Mengirim log ke Telegram menggunakan loop yang sudah berjalan"""
    try:
        # Gunakan loop dari bot_thread
        asyncio.run_coroutine_threadsafe(
            app.send_message(ADMIN_ID, f"🔔 **Update Database:**\n{msg}"),
            bot_loop
        )
    except:
        pass

# --- HANDLER BOT TELEGRAM ---
@app.on_message(filters.command("dblist") & filters.user(ADMIN_ID))
async def list_db_handler(client, message):
    dbs = load_db_list()
    if not dbs:
        await message.reply("Belum ada database tersimpan.")
        return
    res = "**Daftar Database Tersimpan:**\n\n" + "\n".join([f"• `{u}`" for u in dbs])
    await message.reply(res)

# --- CLI MENU ---
def browse_collection(collection):
    cursor = list(collection.find())
    if not cursor:
        print("\n[!] Koleksi ini kosong.")
        input("Tekan Enter...")
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
            confirm = input("Hapus data ini? (y/n): ")
            if confirm == 'y':
                collection.delete_one({"_id": doc["_id"]})
                cursor.pop(index)
                if not cursor: break
                if index >= len(cursor): index -= 1
        elif cmd == 'b':
            break

def cli_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MONGO MANAGER (BOT ACTIVE) ===")
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
                    send_bot_log(f"URL Baru ditambahkan:\n`{url}`")
                    print("Berhasil disimpan.")
                else: print("URL sudah ada.")
            input("\nTekan Enter...")
        elif pilihan == '2':
            dbs = load_db_list()
            if not dbs:
                input("List kosong. Tekan Enter...")
                continue
            for i, url in enumerate(dbs, 1): print(f"{i}. {url[:60]}...")
            try:
                idx = int(input("Pilih nomor: ")) - 1
                client = MongoClient(dbs[idx], serverSelectionTimeoutMS=5000)
                db_names = client.list_database_names()
                for i, n in enumerate(db_names, 1): print(f"{i}. {n}")
                db_sel = client[db_names[int(input("Pilih DB: "))-1]]
                col_names = db_sel.list_collection_names()
                for i, n in enumerate(col_names, 1): print(f"{i}. {n}")
                col_sel = db_sel[col_names[int(input("Pilih Kol: "))-1]]
                browse_collection(col_sel)
            except Exception as e: 
                input(f"Error: {e}. Tekan Enter...")
        elif pilihan == '3':
            dbs = load_db_list()
            for i, url in enumerate(dbs, 1): print(f"{i}. {url[:60]}...")
            try:
                idx = int(input("Hapus nomor: ")) - 1
                removed = dbs.pop(idx)
                save_db_list(dbs)
                send_bot_log(f"URL Dihapus:\n`{removed}`")
                print("Terhapus.")
            except: pass
            input("\nTekan Enter...")
        elif pilihan == '4':
            os._exit(0)

# --- RUNNER LOGIC ---
bot_loop = asyncio.new_event_loop()

def run_bot_worker(loop):
    asyncio.set_event_loop(loop)
    # Start bot tanpa install signal handlers
    loop.run_until_complete(app.start())
    # Menjaga loop tetap berjalan untuk menghandle update Telegram
    loop.run_forever()

if __name__ == "__main__":
    # Jalankan worker di thread terpisah
    t = threading.Thread(target=run_bot_worker, args=(bot_loop,), daemon=True)
    t.start()
    
    # Jalankan CLI di thread utama
    try:
        cli_menu()
    except KeyboardInterrupt:
        os._exit(0)
