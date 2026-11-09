
import csv
import re
import time
import requests

from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/test-sites/e-commerce/static/computers/laptops"
TARGET = 50


def scrape_laptops():
    hasil = []
    halaman = 1
    url_terkumpul = set()

    while len(hasil) < TARGET:
        print(f"Mengambil halaman {halaman}...")

        try:
            response = requests.get(
                BASE_URL,
                params={"page": halaman},
                timeout=15
            )
            response.raise_for_status()

        except requests.RequestException as error:
            print("Gagal mengakses website:", error)
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Mendukung beberapa struktur kartu produk
        cards = soup.select(
            "div.product-wrapper, div.thumbnail"
        )

        if not cards:
            print("Tidak ada kartu produk ditemukan.")
            break

        data_baru = 0

        for card in cards:
            title = card.select_one("a.title")
            price = card.select_one(".price")
            description = card.select_one(".description")

            if not title or not price:
                continue

            nama = title.get("title") or title.get_text(strip=True)
            harga_asli = price.get_text(strip=True)
            spesifikasi = (
                description.get_text(" ", strip=True)
                if description else ""
            )

            url_produk = urljoin(
                response.url,
                title.get("href", "")
            )

            if url_produk in url_terkumpul:
                continue

            # Regex 1: membersihkan format harga
            harga_bersih = re.sub(
                r"[^\d.]",
                "",
                harga_asli
            )

            # Regex 2: mengambil kapasitas RAM
            ram_match = re.search(
                r"\b(\d{1,3})\s*GB\b",
                spesifikasi,
                re.IGNORECASE
            )

            if not harga_bersih:
                continue

            try:
                harga_usd = float(harga_bersih)
            except ValueError:
                continue

            ram_gb = (
                int(ram_match.group(1))
                if ram_match else ""
            )

            hasil.append({
                "id": len(hasil) + 1,
                "nama_laptop": nama,
                "harga_asli": harga_asli,
                "harga_usd": harga_usd,
                "deskripsi": spesifikasi,
                "ram_gb": ram_gb,
                "url_produk": url_produk,
                "tanggal_scraping": datetime.now().isoformat(
                    timespec="seconds"
                )
            })

            url_terkumpul.add(url_produk)
            data_baru += 1

            if len(hasil) >= TARGET:
                break

        print(f"Total data terkumpul: {len(hasil)}")

        if data_baru == 0:
            print("Tidak ada data baru. Proses dihentikan.")
            break

        halaman += 1
        time.sleep(0.5)

    return hasil


def simpan_csv(data):
    if not data:
        print("Dataset kosong, CSV tidak dibuat.")
        return

    folder = Path("output")
    folder.mkdir(parents=True, exist_ok=True)

    file_csv = folder / "hasil_scraping.csv"

    with file_csv.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=data[0].keys()
        )
        writer.writeheader()
        writer.writerows(data)

    print(f"\nFile berhasil disimpan: {file_csv}")


if __name__ == "__main__":
    print("=== LAPTOP PRICE SCRAPER ===")

    laptops = scrape_laptops()
    simpan_csv(laptops)

    print(f"\nTotal data akhir: {len(laptops)}")
