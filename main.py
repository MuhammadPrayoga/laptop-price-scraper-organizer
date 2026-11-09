
import requests
from bs4 import BeautifulSoup

URL = "https://webscraper.io/test-sites/e-commerce/static/computers/laptops"

def scrape_laptops():
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        laptops = soup.select("div.thumbnail")

        print(f"Jumlah laptop ditemukan: {len(laptops)}")
        print("=" * 50)

        for laptop in laptops:
            title = laptop.select_one("a.title")
            price = laptop.select_one("h4.price")
            description = laptop.select_one("p.description")

            if not title or not price:
                continue

            print("Nama  :", title.get("title") or title.get_text(strip=True))
            print("Harga :", price.get_text(strip=True))
            print("Spek  :", description.get_text(strip=True) if description else "-")
            print("-" * 50)

    except requests.RequestException as error:
        print("Gagal mengambil data:", error)

if __name__ == "__main__":
    scrape_laptops()
