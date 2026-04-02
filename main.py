import json
import os
import asyncio
from pymongo import MongoClient
from pyrogram import Client, raw

# --- KONFIGURASI GLOBAL ---
DB_STORAGE_FILE = "databases.json"
TG_STORAGE_FILE = "telegrams.json"

# Menggunakan API ID dan HASH default agar tidak perlu input manual
API_ID = 38478620
API_HASH = "b31e4e594d8ba8847d4084cdd6c18c66"

# --- FUNGSI HELPER DATA ---
def load_data(file_path):
    if not os.path.exists(file_path): 
        return []
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
        input("Tekan Enter untuk kembali...")
        return

    index = 0
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        doc = cursor[index]
        print(f"--- Menampilkan Data {index + 1} dari {len(cursor)} ---")
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

def mongo_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MONGODB MANAGER ===")
        print("1. Masukkan Mongo URL Baru")
        print("2. Lihat Database Tersimpan")
        print("3. Hapus Database dari List")
        print("4. Kembali ke Menu Utama")
        
        pilihan = input("Pilih menu: ")

        if pilihan == '1':
            url = input("Masukkan Mongo URL: ").strip()
            if url:
                dbs = load_data(DB_STORAGE_FILE)
                if url not in dbs:
                    dbs.append(url)
                    save_data(DB_STORAGE_FILE, dbs)
                    print("URL Berhasil disimpan.")
                else:
                    print("URL sudah ada di dalam list.")
            input("\nTekan Enter...")

        elif pilihan == '2':
            dbs = load_data(DB_STORAGE_FILE)
            if not dbs:
                input("List kosong. Masukkan URL terlebih dahulu. (Enter)")
                continue
            
            print("\n--- Pilih Database URL ---")
            for i, url in enumerate(dbs, 1):
                print(f"{i}. {url[:60]}...")
            
            try:
                idx = int(input("\nPilih nomor URL: ")) - 1
                client = MongoClient(dbs[idx], serverSelectionTimeoutMS=5000)
                client.admin.command('ping') # Tes koneksi
                
                db_names = [n for n in client.list_database_names() if n not in ['admin', 'local', 'config']]
                print("\n--- Daftar Database ---")
                for i, n in enumerate(db_names, 1): print(f"{i}. {n}")
                db_sel = client[db_names[int(input("Pilih Nomor DB: "))-1]]
                
                col_names = db_sel.list_collection_names()
                print("\n--- Daftar Koleksi (Folder) ---")
                for i, n in enumerate(col_names, 1): print(f"{i}. {n}")
                col_sel = db_sel[col_names[int(input("Pilih Nomor Koleksi: "))-1]]
                
                browse_collection(col_sel)
            except Exception as e:
                print(f"\n[!] Error koneksi/input: {e}")
                input("Tekan Enter...")

        elif pilihan == '3':
            dbs = load_data(DB_STORAGE_FILE)
            for i, url in enumerate(dbs, 1): print(f"{i}. {url[:60]}...")
            try:
                idx = int(input("\nNomor yang akan dihapus: ")) - 1
                dbs.pop(idx)
                save_data(DB_STORAGE_FILE, dbs)
                print("Berhasil menghapus URL dari list.")
            except: pass
            input("\nTekan Enter...")

        elif pilihan == '4':
            break


# ==========================================
#        BAGIAN 2: MANAJER TELEGRAM
# ==========================================
async def login_telegram():
    print("\n--- Tambah Akun Telegram ---")
    string_session = input("Masukkan Pyrogram String Session: ").strip()
    
    if not string_session:
        print("Sesi tidak boleh kosong!")
        input("\nTekan Enter...")
        return

    try:
        print("\nMencoba masuk...")
        app = Client("temp_session", session_string=string_session, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await app.start()
        me = await app.get_me()
        
        acc_data = {
            "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
            "user_id": me.id,
            "username": me.username or "Tidak Ada",
            "phone": me.phone_number or "Tersembunyi",
            "session": string_session
        }
        
        accounts = load_data(TG_STORAGE_FILE)
        # Cek apakah ID sudah ada di list
        if any(a.get("user_id") == me.id for a in accounts):
            print("Akun ini sudah ada di dalam daftar!")
        else:
            accounts.append(acc_data)
            save_data(TG_STORAGE_FILE, accounts)
            print(f"✅ Berhasil masuk & menyimpan akun: {acc_data['name']}")
        
        await app.stop()
    except Exception as e:
        print(f"❌ Gagal Login: Sesi tidak valid atau kedaluwarsa. ({e})")
    
    input("\nTekan Enter...")

async def manage_account(acc):
    app = Client("active_acc", session_string=acc['session'], api_id=API_ID, api_hash=API_HASH, in_memory=True)
    try:
        await app.start()
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"=== INFO AKUN: {acc['name']} ===")
            print(f"ID Akun  : {acc['user_id']}")
            print(f"Username : @{acc['username']}")
            print(f"Nomor HP : +{acc['phone']}")
            print("-" * 35)
            print("1. Lihat 10 Pesan Terakhir dari Telegram (Kode OTP)")
            print("2. Lihat Sesi Aktif & Berhentikan Sesi Lain")
            print("3. Kembali")
            
            pilih = input("\nPilih menu: ")
            
            if pilih == '1':
                print("\n--- 10 Pesan Terakhir dari Akun Resmi (777000) ---")
                try:
                    async for msg in app.get_chat_history(777000, limit=10):
                        tanggal = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "Waktu Tidak Diketahui"
                        teks = msg.text or "Pesan bukan teks."
                        print(f"[{tanggal}]\n{teks}\n{'-'*30}")
                except Exception as e:
                    print(f"Gagal mengambil pesan: {e}")
                input("\nTekan Enter...")
                
            elif pilih == '2':
                try:
                    sessions = await app.invoke(raw.functions.account.GetAuthorizations())
                    print("\n--- Daftar Sesi Aktif ---")
                    for i, s in enumerate(sessions.authorizations, 1):
                        current = " (Sesi Ini)" if s.current else ""
                        print(f"{i}. {s.device_model} | {s.platform} | {s.ip}{current}")
                    
                    print("\n0. Kembali")
                    print("99. BERHENTIKAN SEMUA SESI LAIN (Kecuali sesi ini)")
                    
                    act = input("\nPilih aksi: ")
                    if act == '99':
                        confirm = input("Yakin mengeluarkan semua perangkat lain? (y/n): ")
                        if confirm == 'y':
                            await app.invoke(raw.functions.auth.ResetAuthorizations())
                            print("✅ Semua sesi lain berhasil diberhentikan.")
                except Exception as e:
                    print(f"Gagal memuat sesi: {e}")
                
                input("\nTekan Enter...")

            elif pilih == '3':
                break
        await app.stop()
    except Exception as e:
        print(f"❌ Error saat memuat akun: {e}")
        input("Sesi mungkin sudah mati. Tekan Enter...")

def telegram_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== TELEGRAM ACCOUNT MANAGER ===")
        print("1. Masukkan String Session Baru")
        print("2. Lihat Akun Tersimpan")
        print("3. Kembali ke Menu Utama")
        
        pilih = input("\nPilih menu: ")
        
        if pilih == '1':
            asyncio.run(login_telegram())
            
        elif pilih == '2':
            accounts = load_data(TG_STORAGE_FILE)
            if not accounts:
                input("Belum ada akun tersimpan. (Enter)")
                continue
            
            os.system('clear' if os.name == 'posix' else 'cls')
            print("--- Daftar Akun Telegram ---")
            for i, acc in enumerate(accounts, 1):
                print(f"{i}. {acc['name']} (+{acc['phone']})")
            
            print("\n0. Kembali")
            try:
                sel = int(input("Pilih Akun untuk dikelola (atau ketik nomor untuk aksi lain): ")) - 1
                if sel == -1: continue
                
                print(f"\nTerpilih: {accounts[sel]['name']}")
                print("1. Masuk & Kelola Akun (OTP, Sesi, Info)")
                print("2. Hapus Akun dari Daftar List")
                sub = input("Pilih aksi: ")
                
                if sub == '1':
                    asyncio.run(manage_account(accounts[sel]))
                elif sub == '2':
                    confirm = input("Hapus akun ini dari database lokal? (y/n): ")
                    if confirm == 'y':
                        accounts.pop(sel)
                        save_data(TG_STORAGE_FILE, accounts)
                        print("✅ Akun berhasil dihapus.")
                        input("Tekan Enter...")
            except: pass
            
        elif pilih == '3':
            break

# ==========================================
#            MAIN RUNNER
# ==========================================
def main_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== MULTI MANAGER SYSTEM ===")
        print("1. MANAGE MONGODB")
        print("2. MANAGE TELEGRAM")
        print("3. KELUAR")
        
        pilih = input("\nPilih Menu: ")
        
        if pilih == '1':
            mongo_menu()
        elif pilih == '2':
            telegram_menu()
        elif pilih == '3':
            print("Menutup program...")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nProgram dihentikan secara paksa.")
