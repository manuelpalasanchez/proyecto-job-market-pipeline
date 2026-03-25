from dotenv import load_dotenv
import os
import requests
from extractors.base_extractor import BaseExtractor

load_dotenv()
class AdzunaExtractor(BaseExtractor):
    """
    Extractor para la API de Adzuna
    """
    URL_BASE = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, country: str = "es", keywords: list[str] = None, max_pages: int = 5, max_days_old: int = 120):
        self.country = country
        self.keywords = keywords or ["data engineer", "data analyst", "python", "sql"]
        self.max_pages = max_pages
        self.max_days_old = max_days_old

        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")

    def _fetch_page(self, keyword:str, page:int)->  dict:
        """
        Lanza una peticion a la API y devuelve Json respuesta
        """
        url = f"{self.URL_BASE}/{self.country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what":keyword,
            "results_per_page": 50,
            "max_days_old": self.max_days_old,
            "content-type": "application/json"   
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _parse_job(self, job: dict) -> dict:
        """
        Mapea resultado de la api
        """
        localizacion = job.get("location", {})
        area = localizacion.get("area", [])
        return {
            "source": "adzuna",
            "external_id": str(job.get("id", "")),
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", ""),
            "location": localizacion.get("display_name", ""),
            "country": area[0] if area else "",
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "description": job.get("description", ""),
            "url": job.get("redirect_url", ""),
            "tags": job.get("category", {}).get("tag", ""),
            "job_type": job.get("category", {}).get("label", ""),
            "contract_time": job.get("contract_time"),
            "contract_type": job.get("contract_type"),
            "created_at": job.get("created"),
        }

    def extract(self) -> list[dict]:
        """
        Itera sobre las keywords,páginas, extrae y normaliza
        """
        all_jobs = []
        for keyword in self.keywords:
            print(f"Extracción de '{keyword}'")
            for page in range(1, self.max_pages + 1):
                try:
                    data = self._fetch_page(keyword, page)
                    jobs = data.get("results", [])
                    if not jobs:
                        print(f"Página {page}: sin resultados, parando")
                        break
                    for job in jobs:
                        parsed_job = self._parse_job(job)
                        all_jobs.append(parsed_job)
                except requests.HTTPError as e:
                    print(f"-Error HTTP en página {page}: {e}")
                    break
                except Exception as e:
                    print(f"-Error inesperado en página {page}: {e}")
                    break
        print(f"\nTotal ofertas extraídas: {len(all_jobs)}")
        return all_jobs