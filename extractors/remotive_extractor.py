import requests
from dotenv import load_dotenv
from extractors.base_extractor import BaseExtractor
import os
import re
from bs4 import BeautifulSoup

load_dotenv()
class RemotiveExtractor(BaseExtractor):
    """
    Extractor para la API de Remotive
    """
    URL_BASE = "https://remotive.com/api/remote-jobs"
    
    def __init__(self, keywords: list[str] = None):
        self.keywords = keywords or ["data engineer", "data analyst", "python", "sql"]

    def _fetch_page(self, keyword:str)->  dict:
        """
        Lanza peticion y devuelve Json respuesta
        """
        url = f"{self.URL_BASE}?search={keyword}"

        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def _parse_job(self, job: dict) -> dict:
        """
        Mapea resultado de la api
        """
        salary = job.get("salary", "")
        salary_min = None
        salary_max = None
        if salary:
            try:
                salary_parts  = (
                    salary.replace("k", "000").replace("$", "").replace(",", "").split("-")
                )
                salary_min = float(salary_parts[0].strip()) if salary_parts[0].strip() else None
                salary_max = float(salary_parts[1].strip()) if len(salary_parts) > 1 else None
            except (ValueError, IndexError):
                pass

        html_desc = job.get("description", "")
        soup = BeautifulSoup(html_desc, "html.parser")
        desc_bruta = soup.get_text(separator="\n").strip()
        lineas_limpias = [line.strip() for line in desc_bruta.splitlines() if line.strip()] 
        desc_limpia = "\n".join(lineas_limpias)    
        return {
            "source": "remotive",
            "external_id": str(job.get("id", "")),
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("candidate_required_location", ""),
            "country": None,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": desc_limpia,
            "url": job.get("url", ""),
            "tags": ", ".join(job.get("tags", [])),
            "job_type": job.get("category", ""),
            "contract_time": None,
            "contract_type": job.get("job_type"),
            "created_at": job.get("publication_date"),
        }
    
    def extract(self) -> list[dict]:
        """
        Extrae ofertas de empleo de la API
        """
        all_jobs = []
        for keyword in self.keywords:
            try:
                data = self._fetch_page(keyword)
                jobs = data.get("jobs", [])
                for job in jobs:
                    parsed_job = self._parse_job(job)
                    all_jobs.append(parsed_job)
            except Exception as e:
                print(f"Error al extraer datos para keyword '{keyword}': {e}")
        return all_jobs
