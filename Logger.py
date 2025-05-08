import os
import json
import csv
import time
from datetime import datetime
from typing import Dict, Iterator, Optional
import zipfile


class Logger:
    def __init__(self, config_path: str):
        """
        Inicjalizuje logger na podstawie pliku JSON.
        :param config_path: Ścieżka do pliku konfiguracyjnego (.json)
        """
        with open(config_path, 'r') as file:
            config = json.load(file)

        self.log_dir = config["log_dir"]
        self.filename_pattern = config["filename_pattern"]
        self.buffer_size = config["buffer_size"]
        self.rotate_every_hours = config["rotate_every_hours"]
        self.max_size_mb = config["max_size_mb"]
        self.rotate_after_lines = config["rotate_after_lines"]
        self.retention_days = config["retention_days"]
        self.current_file = None
        self.buffer = []
        self.line_count = 0  # Licznik linii w pliku

        # Tworzenie katalogów, jeśli nie istnieją
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "archive"), exist_ok=True)

    def start(self) -> None:
        """
        Otwiera nowy plik CSV do logowania. Jeśli plik jest nowy, zapisuje nagłówek.
        """
        filename = datetime.now().strftime(self.filename_pattern)
        file_path = os.path.join(self.log_dir, filename)

        file_exists = os.path.exists(file_path)
        self.current_file = open(file_path, mode='a', newline='', encoding='utf-8')
        if not file_exists:
            writer = csv.writer(self.current_file, delimiter=';')
            writer.writerow(['timestamp', 'sensor_id', 'value', 'unit'])

        # Resetowanie licznika linii przy rozpoczęciu nowego pliku
        self.line_count = 0

    def stop(self) -> None:
        """
        Wymusza zapis bufora i zamyka bieżący plik.
        """
        if self.current_file:
            self._flush_buffer()
            self._check_rotation(force=True)  # Sprawdzenie rotacji przy zamknięciu
            self.current_file.close()
            self.current_file = None

    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str) -> None:
        """
        Dodaje wpis do bufora i ewentualnie wykonuje rotację pliku.
        """
        self.buffer.append([timestamp, sensor_id, value, unit])
        if len(self.buffer) >= self.buffer_size:
            self._flush_buffer()

        self._check_rotation()  # Sprawdzamy rotację po dodaniu wpisu

    def read_logs(self, start: datetime, end: datetime, sensor_id: Optional[str] = None) -> Iterator[Dict]:
        """
        Pobiera wpisy z logów zadanego zakresu i opcjonalnie konkretnego czujnika.
        """
        log_files = self._get_log_files()

        for file_path in log_files:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    timestamp = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                    if start <= timestamp <= end:
                        if sensor_id is None or row['sensor_id'] == sensor_id:
                            yield {
                                'timestamp': timestamp,
                                'sensor_id': row['sensor_id'],
                                'value': float(row['value']),
                                'unit': row['unit']
                            }

    def _flush_buffer(self) -> None:
        """Zapisuje zawartość bufora do pliku."""
        if self.current_file and self.buffer:
            writer = csv.writer(self.current_file, delimiter=';')
            writer.writerows(self.buffer)
            self.line_count += len(self.buffer)  # Zwiększamy licznik linii o liczbę zapisanych wpisów
            self.buffer.clear()

    def _check_rotation(self, force: bool = False) -> None:
        """Sprawdza, czy plik powinien zostać obrócony."""
        if self.current_file and self.buffer:
            file_size = os.path.getsize(self.current_file.name) / (1024 * 1024)  # W MB

            if force or self.line_count >= self.rotate_after_lines or file_size >= self.max_size_mb:
                self._rotate()

    def _rotate(self) -> None:
        """Wykonuje rotację pliku logu."""
        if self.current_file:
            self._flush_buffer()  # Zapisujemy zawartość bufora przed rotacją
            self._archive()  # Archiwizujemy stary plik
            self.start()  # Tworzymy nowy plik

    def _archive(self) -> None:
        """Archiwizuje zamknięty plik logu."""
        if self.current_file:
            filename = self.current_file.name
            archive_dir = os.path.join(self.log_dir, 'archive')
            archive_filename = os.path.basename(filename) + ".zip"
            archive_path = os.path.join(archive_dir, archive_filename)

            # Zamykamy plik przed archiwizacją
            self.current_file.close()
            self.current_file = None

            # Utwórz archiwum zip
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(filename, os.path.basename(filename))

            # Poczekaj chwilę przed usunięciem pliku (daje czas systemowi na zakończenie operacji)
            time.sleep(1)

            # Usuwamy plik po zapisaniu go w archiwum
            os.remove(filename)
            self._clean_old_archives()

    def _clean_old_archives(self) -> None:
        """Usuwa archiwa starsze niż retention_days."""
        archive_dir = os.path.join(self.log_dir, 'archive')
        now = datetime.now()

        for filename in os.listdir(archive_dir):
            file_path = os.path.join(archive_dir, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if (now - file_mtime).days > self.retention_days:
                os.remove(file_path)

    def _get_log_files(self):
        """Zwraca listę plików logów (CSV oraz archiwalne ZIP)."""
        log_files = []
        log_files.extend([os.path.join(self.log_dir, f) for f in os.listdir(self.log_dir) if f.endswith('.csv')])
        archive_dir = os.path.join(self.log_dir, 'archive')
        for zip_file in os.listdir(archive_dir):
            if zip_file.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(archive_dir, zip_file), 'r') as zipf:
                    zipf.extractall(archive_dir)
                    log_files.extend([os.path.join(archive_dir, f) for f in zipf.namelist() if f.endswith('.csv')])
        return log_files
