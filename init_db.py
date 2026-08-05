# init_db.py
from db import engine, Base
import models  # IMPORTANT: You MUST import models before calling create_all!

print("Creating tables in TiDB Cloud...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")