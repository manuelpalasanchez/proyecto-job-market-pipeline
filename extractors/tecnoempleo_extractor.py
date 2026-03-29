import requests
import time
from bs4 import BeautifulSoup
from extractors.base_extractor import BaseExtractor
import re
from datetime import datetime

class TecnoempleoExtractor(BaseExtractor):
    """
    Extractor para Tecnoempleo mediante web scraping
    """
    URL_BASE = "https://www.tecnoempleo.com/"
    URL_BUSQUEDA = "https://www.tecnoempleo.com/busqueda-empleo.php"

    def __init__(self, keywords: list[str] = None, max_pages: int = 5):
        self.keywords = keywords or ["data engineer", "data analyst", "python", "sql"]
        self.max_pages = max_pages
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    def _get_soup(self, url: str, params: dict = None) -> BeautifulSoup | None:
        """
        Hace petición GET y devuelve un objeto BeautifulSoup
        """
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"Error buscando pagina: {e}")
            return None
        
    def _parse_listing_job(self, card) -> dict | None:
        try:
            title_tag = card.select_one("a.font-weight-bold.text-cyan-700")
            if not title_tag:
                return None

            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")
            if not url.startswith("http"):
                url = self.URL_BASE + url

            external_id = url.split("/rf-")[-1].split("?")[0] if "/rf-" in url else ""

            company_tag = card.select_one("a.text-primary.link-muted")
            company = company_tag.get_text(strip=True) if company_tag else ""

            tag_badges = card.select("span.badge.bg-gray-500")
            tags = ", ".join([t.get_text(strip=True) for t in tag_badges])

            return {
                "source": "tecnoempleo",
                "external_id": external_id,
                "title": title,
                "company": company,
                "tags": tags,
                "url": url,
            }

        except Exception as e:
            print(f"  Error parseando tarjeta: {e}")
            return None
        
    def _parse_detail_job(self, url: str) -> dict | None:
        """
        Entra en la página de detalle de una oferta y extrae los campos.
        """
        soup = self._get_soup(url)
        if not soup:
            return None

        try:
            desc_tag = soup.select_one("div[itemprop='description'] p")
            description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else ""

            loc_tag = soup.select_one("a[title*='Ofertas de Empleo en']")
            loc = loc_tag.get_text(strip=True) if loc_tag else ""

            fecha_tag = soup.find("i", class_="fi-calendar")
            created_at_raw = ""
            if fecha_tag and fecha_tag.parent:
                text = fecha_tag.parent.get_text(strip=True)
                match = re.search(r"\d{2}/\d{2}/\d{4}", text)
                created_at_raw = match.group(0) if match else ""
            contract_type = ""
            contract_time = ""
            salary_raw = ""
            job_type = ""
            items = soup.select("ul.list-unstyled li.list-item")

            for item in items:
                label_tag = item.select_one("span.d-inline-block")
                value_tag = item.select_one("span.float-end")

                if not label_tag or not value_tag:
                    continue

                label = label_tag.get_text(strip=True).lower()
                value = value_tag.get_text(strip=True)

                if "contrato" in label:
                    contract_type = value
                elif "jornada" in label:
                    contract_time = value
                elif "funciones" in label:
                    job_type = value

            salary_tag = soup.select_one("li.list-item.clearfix.py-2.mb-3")
            if salary_tag:
                btn = salary_tag.select_one("a.btn")
                if btn:
                    salary_raw = btn.get_text(strip=True)
            return {
                "location": loc,
                "description": description,
                "contract_type": contract_type,
                "contract_time": contract_time,
                "job_type": job_type,
                "salary_raw": salary_raw,
                "created_at_raw": created_at_raw,
            }

        except Exception as e:
            print(f"  Error parseando detalle {url}: {e}")
            return None
        

    def _fetch_listing(self, keyword: str, page: int) -> list[dict]:
        """
        Scrape una página del listado y devuelve lista de jobs básicos.
        """
        params = {"te": keyword, "pagina": page}
        soup = self._get_soup(self.URL_BUSQUEDA, params=params)
        if not soup:
            return []

        cards = soup.select("div.p-3.border.rounded.mb-3.bg-white")
        jobs = []
        for card in cards:
            job = self._parse_listing_job(card)
            if job:
                jobs.append(job)

        return jobs

    def _parse_salary(self, salary_raw: str):
        """
        Convierte salary_raw a min y max numéricos.
        """
        salary_min = None
        salary_max = None

        if not salary_raw:
            return salary_min, salary_max

        try:
            clean = salary_raw.replace("€", "").replace(".", "").replace("b/a", "").strip()
            parts = clean.split("-")
            salary_min = float(parts[0].strip()) if parts[0].strip() else None
            salary_max = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
        except (ValueError, IndexError):
            pass

        return salary_min, salary_max

    def _parse_date(self, date_raw: str):
        """
        Convierte fecha 'dd/mm/yyyy' a objeto datetime.
        """
        if not date_raw:
            return None
        try:
            return datetime.strptime(date_raw, "%d/%m/%Y")
        except ValueError:
            return None

    def extract(self) -> list[dict]:
        """
        Scraping completo — listado + detalle por cada oferta.
        """
        all_jobs = []
        seen_ids = set()

        for keyword in self.keywords:
            print(f"Extrayendo keyword: '{keyword}'")

            for page in range(1, self.max_pages + 1):
                basic_jobs = self._fetch_listing(keyword, page)

                if not basic_jobs:
                    print(f"  Página {page}: sin resultados, parando")
                    break

                print(f"  Página {page}: {len(basic_jobs)} ofertas encontradas")

                for job in basic_jobs:
                    external_id = job.get("external_id", "")

                    if external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)

                    detail = self._parse_detail_job(job["url"])
                    time.sleep(0.5)  

                    if not detail:
                        continue

                    salary_min, salary_max = self._parse_salary(detail.pop("salary_raw", ""))
                    created_at = self._parse_date(detail.pop("created_at_raw", ""))
                    full_job = {
                        **job,
                        **detail,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "created_at": created_at,
                        "contract_time": detail.get("contract_time"),
                        "contract_type": detail.get("contract_type"),
                    }
                    all_jobs.append(full_job)

                print(f"  Página {page}: {len(basic_jobs)} procesadas")

        print(f"\nTotal ofertas extraídas: {len(all_jobs)}")
        return all_jobs