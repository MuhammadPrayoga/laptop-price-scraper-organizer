"""Laptop Price Scraper & Organizer - UTS Automation Systems.

Sumber latihan: https://webscraper.io/test-sites/e-commerce/static/computers/laptops
Mencakup Chapter 9-13: Regex, file I/O, organisasi & ZIP, CLI, web scraping.

Instalasi:
    python -m pip install requests beautifulsoup4

Contoh:
    python main.py --limit 30
    python main.py --keyword ThinkPad --sort asc --limit 20 --backup
    python main.py --input output/hasil_scraping.csv --sort desc --backup
"""

import argparse
import csv
import json
import re
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/test-sites/e-commerce/static/computers/laptops"
PROJECT_DIR = Path(__file__).resolve().parent
CSV_COLUMNS = [
    "id", "nama_laptop", "harga_asli", "harga_usd", "deskripsi",
    "ram_gb", "jumlah_review", "url_produk", "tanggal_scraping",
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scraping, pembersihan, dan perbandingan harga laptop."
    )
    parser.add_argument("--url", default=BASE_URL, help="URL katalog laptop statis")
    parser.add_argument("--limit", type=int, default=30, help="Target record valid (default: 30)")
    parser.add_argument("--keyword", default="", help="Cari pada nama/deskripsi laptop")
    parser.add_argument("--sort", choices=["asc", "desc", "name"], default="asc",
                        help="Urutan harga naik/turun atau nama")
    parser.add_argument("--min-price", type=float, default=None, help="Harga minimum USD")
    parser.add_argument("--max-price", type=float, default=None, help="Harga maksimum USD")
    parser.add_argument("--output", default="output", help="Folder untuk hasil CSV/TXT")
    backup_group = parser.add_mutually_exclusive_group()
    backup_group.add_argument("--backup", dest="backup", action="store_true",
                              help="Buat backup ZIP (aktif secara default)")
    backup_group.add_argument("--no-backup", dest="backup", action="store_false",
                              help="Jalankan tanpa membuat backup ZIP")
    parser.set_defaults(backup=True)
    parser.add_argument("--max-pages", type=int, default=20, help="Batas halaman (default: 20)")
    parser.add_argument("--input", default=None,
                        help="Gunakan CSV yang sudah ada, tanpa mengambil data dari web")
    args = parser.parse_args()

    if args.limit < 1 or args.max_pages < 1:
        parser.error("--limit dan --max-pages harus lebih besar dari 0")
    if args.min_price is not None and args.min_price < 0:
        parser.error("--min-price tidak boleh negatif")
    if args.max_price is not None and args.max_price < 0:
        parser.error("--max-price tidak boleh negatif")
    if (args.min_price is not None and args.max_price is not None
            and args.min_price > args.max_price):
        parser.error("--min-price tidak boleh melebihi --max-price")
    if not args.input and urlsplit(args.url).scheme not in ("https", "http"):
        parser.error("--url harus diawali http:// atau https://")
    return args


def project_path(path):
    """Menggunakan folder project sebagai dasar untuk path relatif."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_DIR / path


def page_url(base_url, page):
    """Menjaga parameter URL lain; halaman pertama tidak memerlukan ?page=1."""
    parts = urlsplit(base_url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    params.pop("page", None)
    if page > 1:
        params["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(params), parts.fragment))


def parse_price(text):
    """Regex 1: '$1,299.99' -> 1299.99 (USD)."""
    clean = re.sub(r"[^0-9.]", "", str(text))
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", clean):
        return None
    return float(clean)


def parse_ram(description):
    """Regex 2: ambil 4GB/8GB/16GB dari deskripsi; kosong jika tak dikenali."""
    match = re.search(r"(?<!\d)(\d{1,2})\s*GB\b", description, re.IGNORECASE)
    return int(match.group(1)) if match else ""


def extract_cards(html, current_url, fetched_at):
    """Mengambil data asli dari HTML, tanpa mengubah harga ke angka."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.thumbnail")
    if not cards:
        cards = soup.select("div.product-wrapper")
    rows = []
    for card in cards:
        title = card.select_one("a.title")
        price = card.select_one(".price")
        if title is None or price is None:
            continue
        description = card.select_one(".description")
        review = card.select_one(".ratings .pull-right")
        if review is None:
            review = card.select_one(".pull-right")
        href = title.get("href", "")
        if not href:
            continue
        rows.append({
            "nama_laptop": title.get("title") or title.get_text(" ", strip=True),
            "harga_asli": price.get_text(" ", strip=True),
            "deskripsi": description.get_text(" ", strip=True) if description else "",
            "review_asli": review.get_text(" ", strip=True) if review else "",
            "url_produk": urljoin(current_url, href),
            "tanggal_scraping": fetched_at,
        })
    return rows


def clean_record(raw):
    """Validasi, normalisasi, dan konversi tipe data."""
    title = re.sub(r"\s+", " ", str(raw.get("nama_laptop", ""))).strip()
    description = re.sub(r"\s+", " ", str(raw.get("deskripsi", ""))).strip()
    price_text = str(raw.get("harga_asli", "")).strip()
    price = parse_price(price_text)
    url = str(raw.get("url_produk", "")).strip()
    if not title or price is None or price < 0 or not url:
        return None

    reviews = str(raw.get("review_asli", raw.get("jumlah_review", "")))
    reviews_match = re.search(r"\d+", reviews)
    count_reviews = int(reviews_match.group()) if reviews_match else ""

    return {
        "id": 0,  # diisi kembali sesudah filter/sort
        "nama_laptop": title,
        "harga_asli": price_text,
        "harga_usd": price,
        "deskripsi": description,
        "ram_gb": parse_ram(description),
        "jumlah_review": count_reviews,
        "url_produk": url,
        "tanggal_scraping": str(raw.get("tanggal_scraping", "")),
    }


def matches_filters(row, args):
    keyword = args.keyword.casefold().strip()
    combined = (row["nama_laptop"] + " " + row["deskripsi"]).casefold()
    if keyword and keyword not in combined:
        return False
    if args.min_price is not None and row["harga_usd"] < args.min_price:
        return False
    if args.max_price is not None and row["harga_usd"] > args.max_price:
        return False
    return True


def scrape_laptops(args):
    """Berhenti setelah limit valid atau halaman habis; cegah duplikat URL."""
    raw_rows, valid_rows, seen_urls, warnings = [], [], set(), []
    pages_fetched = 0
    session = requests.Session()
    session.headers.update({"User-Agent": "LaptopUTSStudyProject/1.0 (Python requests)"})
    try:
        for page in range(1, args.max_pages + 1):
            url = page_url(args.url, page)
            print(f"[SCRAPING] Halaman {page}: {url}")
            try:
                response = session.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as exc:
                warnings.append(f"Koneksi/HTTP gagal pada halaman {page}: {exc}")
                break

            pages_fetched += 1
            items = extract_cards(
                response.text, response.url,
                datetime.now().astimezone().isoformat(timespec="seconds"),
            )
            if not items:
                warnings.append(f"Tidak ada kartu laptop yang terbaca di halaman {page}.")
                break

            new_items = 0
            for item in items:
                link = item["url_produk"]
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                new_items += 1
                raw_rows.append(item)

                cleaned = clean_record(item)
                if cleaned and matches_filters(cleaned, args):
                    valid_rows.append(cleaned)
                    if len(valid_rows) >= args.limit:
                        break

            print(f"           Unik: {len(raw_rows)} | Lolos filter: {len(valid_rows)}")
            if len(valid_rows) >= args.limit:
                break
            if new_items == 0:
                warnings.append("Seluruh data di halaman ini sudah pernah ditemukan.")
                break
            if page < args.max_pages:
                time.sleep(0.5)  # jeda singkat agar tidak membanjiri server
    finally:
        session.close()
    return raw_rows, valid_rows, pages_fetched, warnings


def load_existing_csv(file_path):
    """Mode offline untuk menguji pembacaan file / FileNotFoundError."""
    if not file_path.is_file():
        raise FileNotFoundError(f"File CSV tidak ditemukan: {file_path}")
    with file_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {"nama_laptop", "harga_asli", "url_produk"}.issubset(reader.fieldnames):
            raise ValueError("CSV harus punya kolom nama_laptop, harga_asli, url_produk")
        return list(reader)


def sort_records(rows, sort_option):
    if sort_option == "desc":
        rows.sort(key=lambda row: row["harga_usd"], reverse=True)
    elif sort_option == "name":
        rows.sort(key=lambda row: row["nama_laptop"].casefold())
    else:
        rows.sort(key=lambda row: row["harga_usd"])
    for number, row in enumerate(rows, start=1):
        row["id"] = number


def save_raw(raw_rows, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "raw_data.txt"
    # Satu JSON per baris, masih berupa data ekstraksi sebelum Regex pembersihan.
    with path.open("w", encoding="utf-8") as f:
        for row in raw_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def save_csv(rows, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "hasil_scraping.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_report(rows, raw_count, pages, args, warnings, folder):
    folder.mkdir(parents=True, exist_ok=True)
    prices = [row["harga_usd"] for row in rows]
    cheapest = min(rows, key=lambda row: row["harga_usd"])
    highest = max(rows, key=lambda row: row["harga_usd"])
    text = "\n".join([
        "LAPORAN OTOMATISASI HARGA LAPTOP",
        "=" * 45,
        f"Waktu pemrosesan  : {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Sumber             : {args.input or args.url}",
        f"Halaman diakses    : {pages}",
        f"Data unik ditemukan: {raw_count}",
        f"Data hasil filter  : {len(rows)}",
        f"Kata kunci         : {args.keyword or '(semua)'}",
        f"Urutan             : {args.sort}",
        f"Harga terendah     : ${min(prices):.2f}",
        f"Harga tertinggi    : ${max(prices):.2f}",
        f"Harga rata-rata    : ${sum(prices) / len(prices):.2f}",
        f"Laptop termurah    : {cheapest['nama_laptop']}",
        f"Laptop termahal   : {highest['nama_laptop']}",
        "",
        "CATATAN: Situs latihan; harga bukan harga pasar nyata.",
        "PERINGATAN:",
        *([f"- {w}" for w in warnings] or ["- Tidak ada."]),
        "",
    ])
    path = folder / "laporan.txt"
    path.write_text(text, encoding="utf-8")
    return path, text


def make_backup(files):
    folder = PROJECT_DIR / "backup"
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "backup_data.zip"
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"File untuk backup tidak ditemukan: {path}")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            # Simpan path relatif ke project jika memungkinkan.
            try:
                name_in_zip = path.relative_to(PROJECT_DIR)
            except ValueError:
                name_in_zip = Path("output") / path.name
            zf.write(path, arcname=str(name_in_zip))
    with zipfile.ZipFile(archive) as zf:
        if zf.testzip() is not None:
            raise OSError("Verifikasi arsip ZIP gagal")
    return archive


def main():
    args = parse_arguments()
    output_dir = project_path(args.output)
    data_dir = PROJECT_DIR / "data"

    print("=" * 58)
    print("  LAPTOP PRICE SCRAPER & ORGANIZER - UTS AUTOMATION")
    print("=" * 58)

    try:
        if args.input:
            input_path = project_path(args.input)
            raw_rows = load_existing_csv(input_path)
            pages = 0  # membaca CSV lokal tanpa koneksi
            warnings = []
            rows = []
            for raw in raw_rows:
                clean = clean_record(raw)
                if clean and matches_filters(clean, args):
                    rows.append(clean)
            rows = rows[:args.limit]
            print(f"[INPUT] {len(raw_rows)} baris dibaca dari {input_path}")
        else:
            raw_rows, rows, pages, warnings = scrape_laptops(args)

        if not rows:
            print("[ERROR] Tidak ada record valid setelah pengambilan dan filter.")
            for warning in warnings:
                print("[PERINGATAN]", warning)
            return 2

        sort_records(rows, args.sort)
        raw_path = save_raw(raw_rows, data_dir)
        csv_path = save_csv(rows, output_dir)
        report_path, report = make_report(
            rows, len(raw_rows), pages, args, warnings, output_dir
        )

        print("\n" + report)
        print(f"[OK] Data mentah : {raw_path}")
        print(f"[OK] CSV         : {csv_path}")
        print(f"[OK] Laporan     : {report_path}")
        if args.backup:
            archive = make_backup([raw_path, csv_path, report_path])
            print(f"[OK] Backup ZIP  : {archive}")
        else:
            print("[INFO] Backup dinonaktifkan (--no-backup).")
        if len(rows) < 30:
            print(f"[PERINGATAN] Hasil hanya {len(rows)} record, belum memenuhi target UTS 30 record.")
        if len(rows) < args.limit:
            print(f"[INFO] Target --limit {args.limit} belum tercapai; data yang tersedia disimpan.")
        for warning in warnings:
            print("[PERINGATAN]", warning)
        print("[SELESAI] Semua output yang tersedia sudah disimpan.")
        return 0 if len(rows) >= args.limit else 2

    except (FileNotFoundError, PermissionError, OSError, ValueError,
            UnicodeError, csv.Error) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
