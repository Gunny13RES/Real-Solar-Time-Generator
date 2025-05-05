import tkinter as tk
from datetime import datetime, timezone, timedelta
import math
import threading
import time

def get_equation_of_time(day_of_year):
    B = 2 * math.pi * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

def get_solar_time(longitude):
    now_utc = datetime.now(timezone.utc)
    day_of_year = now_utc.timetuple().tm_yday
    eot = get_equation_of_time(day_of_year)
    longitude_correction = 4 * longitude
    total_minutes = (now_utc.hour * 60 + now_utc.minute + now_utc.second / 60
                     + longitude_correction + eot)
    hours = int(total_minutes // 60) % 24
    minutes = int(total_minutes % 60)
    seconds = int((total_minutes - int(total_minutes)) * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_solar_noon(longitude):
    # Calcola l'orario UTC del mezzogiorno solare
    eot = get_equation_of_time(datetime.utcnow().timetuple().tm_yday)
    # L'orario in cui il Sole è al culmine (in minuti da mezzanotte UTC)
    solar_noon_utc_min = 720 - 4 * longitude - eot
    hours = int(solar_noon_utc_min // 60)
    minutes = int(solar_noon_utc_min % 60)
    return f"{hours:02d}:{minutes:02d} UTC"

def get_solar_altitude(lat, lon):
    now_utc = datetime.now(timezone.utc)
    day_of_year = now_utc.timetuple().tm_yday

    # Declinazione solare approssimata (in radianti)
    decl = 23.44 * math.pi / 180 * math.sin(2 * math.pi * (284 + day_of_year) / 365)

    # Tempo solare vero (in gradi) da mezzogiorno locale
    eot = get_equation_of_time(day_of_year)
    time_offset = (4 * lon + eot)  # minuti
    t = now_utc.hour * 60 + now_utc.minute + now_utc.second / 60 + time_offset
    ha = math.radians((t / 4 - 180))  # angolo orario in radianti

    # Latitudine in radianti
    lat_rad = math.radians(lat)

    # Altitudine solare (elevazione sopra l'orizzonte)
    altitude = math.asin(math.sin(lat_rad) * math.sin(decl) +
                         math.cos(lat_rad) * math.cos(decl) * math.cos(ha))
    return round(math.degrees(altitude), 2)

class SolarTimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ora Solare Vera + Info Astronomiche")
        self.root.geometry("450x300")

        tk.Label(root, text="Latitudine:").pack()
        self.lat_entry = tk.Entry(root)
        self.lat_entry.pack()

        tk.Label(root, text="Longitudine:").pack()
        self.lon_entry = tk.Entry(root)
        self.lon_entry.pack()

        self.start_button = tk.Button(root, text="Calcola", command=self.start_display)
        self.start_button.pack(pady=10)

        self.time_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.time_label.pack()

        self.altitude_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.altitude_label.pack()

        self.noon_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.noon_label.pack()

        self.running = False

    def start_display(self):
        try:
            self.lat = float(self.lat_entry.get())
            self.lon = float(self.lon_entry.get())
            self.running = True
            threading.Thread(target=self.update_info, daemon=True).start()
        except ValueError:
            self.time_label.config(text="Errore: inserire valori numerici validi.")

    def update_info(self):
        while self.running:
            solar_time = get_solar_time(self.lon)
            solar_alt = get_solar_altitude(self.lat, self.lon)
            solar_noon = get_solar_noon(self.lon)

            self.time_label.config(text=f"🕒 Ora solare vera: {solar_time}")
            self.altitude_label.config(text=f"🌞 Altitudine del Sole: {solar_alt}°")
            self.noon_label.config(text=f"🌅 Mezzogiorno solare (UTC): {solar_noon}")
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = SolarTimeApp(root)
    root.mainloop()

