from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

class PostgresLoader:
    """
    Carga ofertas limpias en la BD Postgres. Se conecta a la base de datos usando SQLAlchemy y ejecuta inserciones.
    """
    def __init__(self):
        self.engine = self._create_engine()

    def _create_engine(self):
        DB_URL = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
            f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        return create_engine(DB_URL)
    
    def initialize_db(self):
        """
        Crea la tabla jobs si no existe
        """
        try:
            with open("database/schema.sql", "r") as f:
                schema = f.read()
            with self.engine.connect() as conn:
                for statement in schema.split(";"):
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                conn.commit()
                print("BD inicializada")
        except Exception as e:
            print(f"Error al inicializar la BD: {e}")

    def load(self, jobs: list[dict]):
        """
        Inserta una lista de ofertas limpias 
        """
        insertados= 0
        saltados= 0
        insert_sql = text("""
            INSERT INTO jobs (
                source, external_id, title, company, location, country,
                salary_min,salary_max, description, url, tags, job_type,
                contract_time, contract_type, created_at)
            VALUES (
                :source, :external_id, :title, :company, :location, :country,
                :salary_min, :salary_max, :description, :url, :tags, :job_type,
                :contract_time, :contract_type, :created_at
            )
            ON CONFLICT (source, external_id) DO NOTHING
        """)
        # Equiv a un ON CONFLICT ON CONSTRAINT uq_source_external_id DO NOTHING
        with self.engine.connect() as conn:
            for job in jobs:
                try:
                    result = conn.execute(insert_sql, job)
                    if result.rowcount == 1:
                        insertados += 1
                    else:
                        saltados += 1
                except Exception as e:
                    print(f"Error al insertar oferta {job.get('external_id')}: {e}")
            conn.commit()

        print(f"Ofertas insertadas: {insertados}, ofertas saltadas por duplicado: {saltados}")