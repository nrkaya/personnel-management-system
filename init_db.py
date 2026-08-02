import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT UNIQUE NOT NULL,
        sifre_hash TEXT NOT NULL
    )
    ''')

    # Personnel table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Personeller (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        soyad TEXT NOT NULL,
        departman TEXT,
        pozisyon TEXT,
        telefon TEXT,
        ek_bilgi TEXT,
        aktif_mi INTEGER DEFAULT 1
    )
    ''')

    # Audit logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Loglar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT NOT NULL,
        tarih_saat DATETIME DEFAULT CURRENT_TIMESTAMP,
        islem_tipi TEXT NOT NULL,
        detay TEXT
    )
    ''')

    # Create default admin user if not exists
    cursor.execute("SELECT id FROM Kullanicilar WHERE kullanici_adi = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cursor.execute("INSERT INTO Kullanicilar (kullanici_adi, sifre_hash) VALUES (?, ?)", ('admin', hashed_pw))
        print("Default admin created: admin / admin123")

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()
