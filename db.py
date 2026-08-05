import certifi
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://4Q6MMMYTALcGNGe.root:WoWo47sYUSJFJjQs@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=/etc/ssl/cert.pem&ssl_verify_cert=true&ssl_verify_identity=true"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl": {
            "ca": certifi.where(),
            "check_hostname": True,
        }
    }
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()