import sqlite3
from datetime import datetime

def upgrade_v3():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Add new columns to Personeller
    cols_to_add = [
        ("avatar_path", "TEXT DEFAULT 'default.png'"),
        ("ise_giris_tarihi", "DATE"),
        ("maas", "REAL")
    ]
    
    for col_name, col_type in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE Personeller ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Create Izinler table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Izinler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personel_id INTEGER NOT NULL,
        baslangic DATE NOT NULL,
        bitis DATE NOT NULL,
        tur TEXT NOT NULL,
        durum TEXT DEFAULT 'Onaylandı',
        kullanici_adi TEXT,
        eklenme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(personel_id) REFERENCES Personeller(id)
    )
    ''')
    
    # Backfill missing hire dates
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("UPDATE Personeller SET ise_giris_tarihi = ? WHERE ise_giris_tarihi IS NULL", (today,))

    conn.commit()
    conn.close()
    print("Schema v3 migration complete.")

if __name__ == '__main__':
    upgrade_v3()
