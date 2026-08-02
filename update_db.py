import sqlite3

def update():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Try to add the 'rol' column. If it already exists, sqlite3 will throw an operational error, which we ignore.
    try:
        cursor.execute("ALTER TABLE Kullanicilar ADD COLUMN rol TEXT DEFAULT 'user'")
        print("Kullanicilar tablosuna 'rol' kolonu eklendi.")
    except sqlite3.OperationalError:
        print("'rol' kolonu zaten mevcut.")
        
    # Update admin user's role to 'admin'
    cursor.execute("UPDATE Kullanicilar SET rol = 'admin' WHERE kullanici_adi = 'admin'")
    
    conn.commit()
    conn.close()
    print("Veritabanı başarıyla güncellendi.")

if __name__ == '__main__':
    update()
