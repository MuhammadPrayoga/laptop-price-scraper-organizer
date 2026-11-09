# Laptop Price Scraper & Organizer

Aplikasi **Command Line Interface (CLI)** berbasis Python untuk mengambil, membersihkan, menyaring, mengurutkan, dan menyimpan data harga laptop secara otomatis. Proyek ini dibuat sebagai implementasi materi **UTS Automation Systems**.

## Sumber data

- Website: [Web Scraper E-commerce Test Site – Laptops](https://webscraper.io/test-sites/e-commerce/static/computers/laptops)
- Jenis data: katalog laptop untuk latihan web scraping.
- Informasi yang diambil: nama laptop, harga, deskripsi, jumlah ulasan, URL produk, dan waktu scraping.
- Informasi tambahan hasil pemrosesan: harga numerik dalam USD serta kapasitas RAM jika tercantum dalam deskripsi.

> **Catatan:** Website tersebut adalah situs latihan. Harga yang tercantum **bukan harga pasar aktual**. Aplikasi ini adalah prototipe pengambilan dan perbandingan data, bukan alat pemantauan harga toko sungguhan.

## Fitur

1. Mengambil data laptop dari beberapa halaman (**pagination**) menggunakan `requests` dan `BeautifulSoup`.
2. Membersihkan format harga, menormalkan spasi, dan mengekstrak kapasitas RAM menggunakan **Regular Expressions (Regex)**.
3. Memfilter data menurut kata kunci serta rentang harga USD.
4. Mengurutkan hasil menurut harga termurah (`asc`), termahal (`desc`), atau nama (`name`).
5. Menyimpan data mentah ke `data/raw_data.txt` dan hasil olahan ke `output/hasil_scraping.csv`.
6. Membuat ringkasan statistik pada `output/laporan.txt` dan menampilkannya di terminal.
7. Membuat folder yang diperlukan secara otomatis dengan `pathlib`.
8. Membuat serta memverifikasi backup `backup/backup_data.zip` secara otomatis setelah pemrosesan berhasil (kecuali memakai `--no-backup`).
9. Membaca kembali CSV yang sudah tersimpan menggunakan `--input`, tanpa koneksi ke website.
10. Menangani kesalahan koneksi, hasil kosong, file tidak ditemukan, serta argumen yang tidak valid.

## Implementasi materi perkuliahan

| Chapter | Materi | Implementasi |
|---|---|---|
| 9 | Regular Expressions | `re.sub()`, `re.fullmatch()`, `re.search()` untuk harga, RAM, spasi, dan ulasan |
| 10 | Reading and Writing Files | `pathlib`, pembacaan/penulisan CSV, TXT, dan laporan |
| 11 | Organizing Files | Membuat direktori dan backup ZIP melalui `zipfile` |
| 12 | Command Line Programs | `argparse` dan argumen CLI |
| 13 | Web Scraping | `requests`, `BeautifulSoup`, dan pagination |

## Persyaratan

- Python 3.9 atau lebih baru (disarankan Python 3.10+).
- Koneksi internet untuk mode scraping.
- Library `requests` dan `beautifulsoup4`.

## Instalasi

### 1. Clone repository

```bash
git clone https://github.com/MuhammadPrayoga/laptop-price-scraper-organizer.git
cd laptop-price-scraper-organizer
```

### 2. Buat virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt (CMD):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instal dependency

```bash
python -m pip install -r requirements.txt
```

## Cara penggunaan

**Pengaturan default:** target **30 laptop**, CSV dan laporan TXT tersimpan, dan backup ZIP dibuat secara otomatis.

```bash
python main.py
```

### Mengambil 30 laptop dan membuat backup otomatis

```bash
python main.py
```

### Filter nama/deskripsi laptop

```bash
python main.py --keyword ThinkPad --limit 30 --backup
```

### Mengurutkan harga tertinggi ke terendah

```bash
python main.py --limit 30 --sort desc
```

### Filter harga dalam USD

```bash
python main.py --limit 30 --min-price 500 --max-price 1000 --backup
```

### Menentukan folder hasil

```bash
python main.py --limit 30 --output hasil_laptop --backup
```

### Membatasi jumlah halaman yang diakses

```bash
python main.py --limit 30 --max-pages 10
```

### Memproses kembali CSV lokal tanpa web scraping

Jalankan perintah ini **setelah CSV dihasilkan**:

```bash
python main.py --input output/hasil_scraping.csv --limit 30 --sort name --backup
```

### Melihat daftar argumen

```bash
python main.py --help
```

## Referensi argumen CLI

| Argumen | Keterangan | Default |
|---|---|---|
| `--url` | URL awal katalog laptop | URL situs latihan |
| `--limit` | Target jumlah **record valid yang lolos filter** | `30` |
| `--keyword` | Kata kunci pada nama atau deskripsi | Tanpa filter |
| `--sort` | `asc`, `desc`, atau `name` | `asc` |
| `--min-price` | Harga minimum dalam USD | Tanpa batas |
| `--max-price` | Harga maksimum dalam USD | Tanpa batas |
| `--output` | Nama/path folder output | `output` |
| `--backup` | Membuat backup ZIP (opsional, tetap tersedia) | Aktif |
| `--no-backup` | Nonaktifkan backup ZIP | Tidak aktif |
| `--max-pages` | Batas maksimum halaman scraping | `20` |
| `--input` | Path CSV lokal untuk diproses ulang | Scraping website |

**Penting:** `--limit 30` adalah target, bukan jaminan mendapatkan 30 produk. Filter yang ketat, kegagalan koneksi, atau jumlah halaman yang terlalu sedikit bisa menyebabkan hasil kurang dari target. Untuk demonstrasi syarat minimal 30 record UTS, gunakan perintah tanpa filter kata kunci/harga.

## Struktur project

```text
laptop-price-scraper-organizer/
├── main.py
├── requirements.txt
├── README.md
├── data/                         # dibuat otomatis
│   └── raw_data.txt             # JSON per baris dari HTML
├── output/                       # dibuat otomatis
│   ├── hasil_scraping.csv
│   └── laporan.txt
├── backup/                       # dibuat otomatis secara default
│   └── backup_data.zip
└── dokumentasi/                  # ditambahkan untuk pengumpulan UTS
    ├── laporan_uts.pdf
    └── video_demo.mp4
```

Folder dan file output dibuat saat program dijalankan dengan data yang valid. Jangan unggah `.venv/`, kredensial, atau file rahasia ke repository GitHub. Folder `dokumentasi/` serta isinya perlu dilengkapi secara terpisah untuk pengumpulan UTS.

## Penjelasan file output

- **`data/raw_data.txt`**: data ekstraksi awal dalam format *JSON Lines* (satu objek JSON per baris), sebelum pembersihan dan filtering.
- **`output/hasil_scraping.csv`**: data hasil pembersihan yang sudah difilter dan diurutkan. Kolomnya meliputi `id`, `nama_laptop`, `harga_asli`, `harga_usd`, `deskripsi`, `ram_gb`, `jumlah_review`, `url_produk`, dan `tanggal_scraping`.
- **`output/laporan.txt`**: ringkasan jumlah data, pengaturan filter, statistik harga, laptop termurah/termahal, dan peringatan bila ada.
- **`backup/backup_data.zip`**: arsip cadangan ketiga file di atas.

**Catatan:** Menjalankan program kembali dapat menimpa CSV, laporan, dan arsip ZIP yang sudah ada. Salin hasil penting ke lokasi lain sebelum pengujian berikutnya.

## Pengujian dasar

Jalankan perintah berikut satu per satu:

```bash
# 1. Tampilkan bantuan CLI
python main.py --help

# 2. Scraping minimal 30 record, jika sumber tersedia
python main.py --limit 30 --backup

# 3. Urutkan berdasarkan nama dari file CSV lokal
python main.py --input output/hasil_scraping.csv --limit 30 --sort name

# 4. Uji file tidak ditemukan
python main.py --input file_tidak_ada.csv

# 5. Uji validasi argumen
python main.py --limit 0
```

Hasil aktual scraping bergantung pada akses internet dan struktur website saat eksekusi. Untuk membuktikan persyaratan UTS, periksa jumlah baris dataset, isi ZIP, serta tampilan terminal.

## Etika penggunaan

- Gunakan hanya untuk pembelajaran dan sumber yang mengizinkan akses.
- Jangan melewati login, CAPTCHA, atau pembatasan situs.
- Hindari permintaan berlebihan; program menggunakan jeda antarhalaman.
- Jangan mengumpulkan data pribadi sensitif.

## Informasi akademik

- Mata kuliah: Automation Systems
- Bentuk tugas: Ujian Tengah Semester (proyek kelompok)
- Program studi: Teknik Informatika
- Universitas: Universitas Pelita Bangsa

Nama anggota dan nomor kelompok dapat ditambahkan setelah data kelompok ditetapkan.
