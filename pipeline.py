from extractors.adzuna_extractor import AdzunaExtractor
from transformers.job_transformer import JobTransformer
from loaders.postgres_loader import PostgresLoader
from extractors.remotive_extractor import RemotiveExtractor

def run_pipeline():
    print("Iniciando pipeline ETL de ofertas de empleo")
    loader = PostgresLoader()
    loader.initialize_db()

    transformer = JobTransformer()

    total_insertados = 0
    total_saltados = 0

    extractors = [
        AdzunaExtractor(
            keywords=["data engineer", "data analyst"],#, "python", "sql", "machine learning"],
            max_pages=5,
            max_days_old=120
        ),
        RemotiveExtractor(
        keywords=["data engineer", "data analyst", "python", "sql"]
    ),
    ]

    for extractor in extractors:
        source = extractor.__class__.__name__
        raw_jobs = extractor.extract()
        clean_jobs = transformer.transform(raw_jobs)
        result = loader.load(clean_jobs)

        total_insertados += result["insertados"]
        total_saltados += result["saltados"]

        print(f"Fuente: {source} - Insertados: {result['insertados']} - Saltados: {result['saltados']}")
    
    print(f"Total insertados: {total_insertados} - Total saltados: {total_saltados}")

if __name__ == "__main__":
    run_pipeline()