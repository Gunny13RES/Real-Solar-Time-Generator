import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone, timedelta
import math
import threading
import time
from geopy.geocoders import Nominatim
from astral import LocationInfo
from astral.sun import sun
import pytz

def get_equation_of_time(day_of_year):
    B = 2 * math.pi * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

def get_solar_time(longitude, date_time):
    day_of_year = date_time.timetuple().tm_yday
    eot = get_equation_of_time(day_of_year)
    longitude_correction = 4 * longitude
    total_minutes = (date_time.hour * 60 + date_time.minute + date_time.second / 60
                     + longitude_correction + eot)
    hours = int(total_minutes // 60) % 24
    minutes = int(total_minutes % 60)
    seconds = int((total_minutes - int(total_minutes)) * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_solar_noon(longitude, date_time):
    eot = get_equation_of_time(date_time.timetuple().tm_yday)
    solar_noon_utc_min = 720 - 4 * longitude - eot
    hours = int(solar_noon_utc_min // 60)
    minutes = int(solar_noon_utc_min % 60)
    return f"{hours:02d}:{minutes:02d} UTC"

def get_solar_altitude(lat, lon, date_time):
    day_of_year = date_time.timetuple().tm_yday
    decl = 23.44 * math.pi / 180 * math.sin(2 * math.pi * (284 + day_of_year) / 365)
    eot = get_equation_of_time(day_of_year)
    time_offset = (4 * lon + eot)
    t = date_time.hour * 60 + date_time.minute + date_time.second / 60 + time_offset
    ha = math.radians((t / 4 - 180))
    lat_rad = math.radians(lat)
    altitude = math.asin(math.sin(lat_rad) * math.sin(decl) +
                         math.cos(lat_rad) * math.cos(decl) * math.cos(ha))
    return round(math.degrees(altitude), 2)

class SolarTimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ora Solare Vera + Info Astronomiche")
        self.root.geometry("520x420")

        try:
            icon = tk.PhotoImage(file="icon.png")
            self.root.iconphoto(True, icon)
        except Exception as e:
            print("Impossibile caricare l'icona:", e)

        tk.Label(root, text="Latitudine (opzionale):").pack()
        self.lat_entry = tk.Entry(root)
        self.lat_entry.pack()

        tk.Label(root, text="Longitudine (opzionale):").pack()
        self.lon_entry = tk.Entry(root)
        self.lon_entry.pack()

        tk.Label(root, text="Oppure inserisci la località:").pack()
        self.location_entry = tk.Entry(root)
        self.location_entry.pack()

        tk.Label(root, text="Data (GG-MM-AAAA):").pack()
        self.date_entry = tk.Entry(root)
        self.date_entry.insert(0, datetime.utcnow().strftime("%d-%m-%Y"))
        self.date_entry.pack()

        tk.Label(root, text="Tipo di ora:").pack()
        self.time_type = tk.StringVar(value="solare")
        ttk.Combobox(root, textvariable=self.time_type, values=["solare", "legale"]).pack()

        self.start_button = tk.Button(root, text="Calcola", command=self.start_display)
        self.start_button.pack(pady=10)

        self.time_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.time_label.pack()

        self.altitude_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.altitude_label.pack()

        self.noon_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.noon_label.pack()

        self.info_label = tk.Label(root, text="", font=("Helvetica", 10), fg="blue")
        self.info_label.pack(pady=5)

        self.running = False

    def get_coordinates(self):
        try:
            if self.lat_entry.get() and self.lon_entry.get():
                lat = float(self.lat_entry.get())
                lon = float(self.lon_entry.get())
            elif self.location_entry.get():
                geolocator = Nominatim(user_agent="solar_app")
                location = geolocator.geocode(self.location_entry.get())
                if location:
                    lat, lon = location.latitude, location.longitude
                else:
                    raise ValueError("Località non trovata.")
            else:
                raise ValueError("Inserire coordinate o località.")
            return lat, lon
        except Exception as e:
            self.time_label.config(text=f"Errore: {e}")
            return None, None

    def start_display(self):
        try:
            lat, lon = self.get_coordinates()
            if lat is None or lon is None:
                return
            self.lat = lat
            self.lon = lon
            self.date = datetime.strptime(self.date_entry.get(), "%d-%m-%Y")
            self.running = True
            threading.Thread(target=self.update_info, daemon=True).start()
        except ValueError:
            self.time_label.config(text="Errore: controlla i dati inseriti.")

    def update_info(self):
        while self.running:
            now_utc = datetime.utcnow()
            date_time = self.date.replace(hour=now_utc.hour, minute=now_utc.minute,
                                          second=now_utc.second, tzinfo=timezone.utc)

            solar_time = get_solar_time(self.lon, date_time)
            solar_alt = get_solar_altitude(self.lat, self.lon, date_time)
            solar_noon = get_solar_noon(self.lon, date_time)

            # Ora di visualizzazione (solare o legale)
            if self.time_type.get() == "legale":
                display_dt = date_time + timedelta(hours=1)
                display_time = get_solar_time(self.lon, display_dt)
                ora_tipo = "(ora legale: +1h rispetto all'ora solare)"
            else:
                display_time = solar_time
                ora_tipo = "(ora solare vera basata sul Sole)"

            date_str = self.date.strftime("%d-%m-%Y")

            self.time_label.config(text=f"🕒 Ora selezionata ({date_str}): {display_time}")
            self.altitude_label.config(text=f"☼ Altitudine del Sole: {solar_alt}°")
            self.noon_label.config(text=f"⌚ Mezzogiorno solare (UTC): {solar_noon}")
            self.info_label.config(text=ora_tipo)

            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = SolarTimeApp(root)
    root.mainloop()
