import sqlite3
import os

def clean_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Remove personnel, leaves, and logs
    cursor.execute('DELETE FROM Personeller')
    cursor.execute('DELETE FROM Izinler')
    cursor.execute('DELETE FROM Loglar')
    
    # Reset SQLite autoincrement sequences
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('Personeller', 'Izinler', 'Loglar')")
    
    cursor.execute("INSERT INTO Loglar (kullanici_adi, islem_tipi, detay) VALUES ('admin', 'Sistem Sıfırlama', 'Örnek veriler temizlendi, sistem sıfırlandı.')")
    
    conn.commit()
    conn.close()
    
    # Clear uploaded avatar images except default.png
    upload_dir = os.path.join('static', 'uploads')
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            if f != 'default.png':
                file_path = os.path.join(upload_dir, f)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Failed to remove {f}: {e}")
                        
    print("Database and uploaded files successfully cleaned.")

if __name__ == '__main__':
    clean_database()
