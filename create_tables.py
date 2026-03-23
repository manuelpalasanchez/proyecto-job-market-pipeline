from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(DB_URL)


try:
    with open("database/schema.sql", "r") as f:
        schema = f.read()

    with engine.connect() as conn:
        conn.execute(text(schema))
        conn.commit()
        print("Tabla creada")

except FileNotFoundError as e:
    print(f"Error:No se encuentra el archivo de esquema {e}")
except Exception as e:
    print(f"Error al crear tabla: {e}")
