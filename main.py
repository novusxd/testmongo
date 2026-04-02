import json
import os
import asyncio
from pymongo import MongoClient
# Menggunakan Hydrogram sebagai pengganti Pyrogram
from hydrogram import Client, raw

# --- KONFIGURASI GLOBAL ---
DB_STORAGE_FILE = "databases.json"
TG_STORAGE_FILE = "telegrams.json"

# API ID dan HASH (Tetap sama)
API_ID = 38478620
API_HASH = "b31e4e594d8ba8847d4084cdd6c18c66"

# --- FUNGSI HELPER DATA ---
def load_data(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, "r") as f:
        try: return json.load(f)
        except: return []

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ==========================================
#        BAGIAN 1: MANAJER MONGODB
# ==========================================
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
        if cmd == 'n' and index < len(cursor) - 1: index += 1
        elif cmd == 'p' and index > 0: index -= 1
        elif cmd == 'd':
            if input("Hapus? (y/n): ") == 'y':
                collection.delete_one({"_id": doc["_id"]})
                cursor.pop(index)
                if not cursor: break
                if index >= len(cursor): index -= 1
        elif cmd == 'b': break

def mongo_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MONGODB MANAGER ===")
        print("1. Masukkan Mongo URL Baru\n2. Lihat Database\n3. Hapus URL\n4. Kembali")
        p = input("Pilih: ")
        if p == '1':
            url = input("Mongo URL: ").strip()
            if url:
                dbs = load_data(DB_STORAGE_FILE)
                if url not in dbs:
                    dbs.append(url)
                    save_data(DB_STORAGE_FILE, dbs)
            input("Tersimpan. Enter...")
        elif p == '2':
            dbs = load_data(DB_STORAGE_FILE)
            if not dbs: continue
            for i, u in enumerate(dbs, 1): print(f"{i}. {u[:50]}...")
            try:
                idx = int(input("Pilih No: ")) - 1
                client = MongoClient(dbs[idx], serverSelectionTimeoutMS=5000)
                db_n = [n for n in client.list_database_names() if n not in ['admin','local','config']]
                for i, n in enumerate(db_n, 1): print(f"{i}. {n}")
                db_sel = client[db_n[int(input("Pilih DB: "))-1]]
                col_n = db_sel.list_collection_names()
                for i, n in enumerate(col_n, 1): print(f"{i}. {n}")
                col_sel = db_sel[col_n[int(input("Pilih Koleksi: "))-1]]
                browse_collection(col_sel)
            except: input("Error. Enter...")
        elif p == '4': break

# ==========================================
#        BAGIAN 2: MANAJER TELEGRAM
# ==========================================
async def login_telegram():
    print("\n--- Login Sesi Baru ---")
    ss = input("String Session: ").strip()
    if not ss: return
    try:
        app = Client("temp", session_string=ss, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await app.start()
        me = await app.get_me()
        acc = {
            "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
            "user_id": me.id,
            "username": me.username or "None",
            "phone": me.phone_number or "N/A",
            "session": ss
        }
        data = load_data(TG_STORAGE_FILE)
        if not any(a['user_id'] == me.id for a in data):
            data.append(acc)
            save_data(TG_STORAGE_FILE, data)
            print(f"✅ Tersimpan: {acc['name']}")
        else: print("Akun sudah ada.")
        await app.stop()
    except Exception as e: print(f"Gagal: {e}")
    input("Enter...")

async def manage_account(acc):
    app = Client("active", session_string=acc['session'], api_id=API_ID, api_hash=API_HASH, in_memory=True)
    try:
        await app.start()
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"=== INFO: {acc['name']} | ID: {acc['user_id']} ===")
            print("-" * 35)
            print("1. Lihat 1 Pesan OTP Terbaru (777000)")
            print("2. Berhentikan Sesi Lain\n3. Kembali")
            p = input("\nPilih: ")
            
            if p == '1':
                print("\n--- OTP TERBARU (777000) ---")
                try:
                    # Mengambil hanya 1 pesan terbaru
                    async for msg in app.get_chat_history(777000, limit=1):
                        tgl = msg.date.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{tgl}]\n{msg.text or 'Bukan teks'}\n{'-'*40}")
                        break
                    else: print("Tidak ada pesan.")
                except Exception as e: print(f"Error: {e}")
                input("Enter...")
            elif p == '2':
                if input("Keluarkan sesi lain? (y/n): ") == 'y':
                    try:
                        await app.invoke(raw.functions.auth.ResetAuthorizations())
                        print("✅ Sesi lain dibersihkan.")
                    except: print("Gagal reset.")
                input("Enter...")
            elif p == '3': break
        await app.stop()
    except: input("Sesi Mati. Enter...")

def telegram_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== TELEGRAM MANAGER ===")
        print("1. Simpan Sesi Baru\n2. List Akun\n3. Kembali")
        p = input("Pilih: ")
        if p == '1': asyncio.run(login_telegram())
        elif p == '2':
            accs = load_data(TG_STORAGE_FILE)
            for i, a in enumerate(accs, 1): print(f"{i}. {a['name']} (+{a['phone']})")
            try:
                idx = int(input("\nPilih No (0 kembali): ")) - 1
                if idx == -1: continue
                print(f"1. Kelola Akun\n2. Hapus Akun")
                sub = input("Aksi: ")
                if sub == '1': asyncio.run(manage_account(accs[idx]))
                elif sub == '2':
                    if input("Hapus? (y/n): ") == 'y':
                        accs.pop(idx)
                        save_data(TG_STORAGE_FILE, accs)
            except: pass
        elif p == '3': break

def main():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MULTI MANAGER 2026 ===")
        print("1. MANAGE MONGO\n2. MANAGE TELEGRAM\n3. KELUAR")
        p = input("Pilih: ")
        if p == '1': mongo_menu()
        elif p == '2': telegram_menu()
        elif p == '3': break

if __name__ == "__main__":
    main()
