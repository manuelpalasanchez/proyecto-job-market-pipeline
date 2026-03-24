from datetime import datetime

class JobTransformer:
    """
    Transforma y limpia los datos crudos de las extracciones al esquema normalizado para cargar en base de datos
    """

    def transform(self, raw_jobs: list[dict]) -> list[dict]:
        """
        A partir de lista de ofertas en crudo genera una lista de ofertas transformadas al esquema normalizado
        """
        transformed_jobs = []
        for job in raw_jobs:
           try:
               clean_job = self._transform_job(job)
               if clean_job:
                   transformed_jobs.append(clean_job)
           except Exception as e:
               print(f"Error al transformar la oferta: {e}")
               continue
           
        print(f"Ofertas transformadas: {len(transformed_jobs)} / {len(raw_jobs)}")
        return transformed_jobs

    def _transform_job(self, job: dict) -> dict | None:
        """
        Transforma una oferta en crudo al modelo normalizado
        """
        titulo = self._clean_string(job.get("title"))
        empresa = self._clean_string(job.get("company"))
        
        if not titulo or not empresa:
            return None
        
        return {
            "source": job.get("source"),
            "external_id": self._clean_string(job.get("external_id")),
            "title": titulo,
            "company": empresa,
            "location": self._clean_string(job.get("location")),
            "country": self._clean_string(job.get("country")),
            "salary_min": self._clean_num(job.get("salary_min")),
            "salary_max": self._clean_num(job.get("salary_max")),
            "description": self._clean_string(job.get("description")),
            "url": self._clean_string(job.get("url")),
            "tags": self._clean_string(job.get("tags")),
            "job_type": self._clean_string(job.get("job_type")),
            "contract_time": self._clean_string(job.get("contract_time")),
            "contract_type": self._clean_string(job.get("contract_type")),
            "created_at": self._parse_date(job.get("created_at")),
        }
    
    def _clean_string(self, value) -> str | None:
        if value is None:
            return None
        limpio = str(value).strip()
        return limpio if limpio else None
    
    def _clean_num(self, value) -> float | None:
        if value is None:
            return None
        try:
            res = float(value)
            return res if res >= 0 else None
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value) -> datetime | None:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None