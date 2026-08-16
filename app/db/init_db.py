from app.db.database import Database

from app.db.models import ReceiptItemORM, ReceiptORM

def init_database() -> None:
    database = Database()
    database.create_tables()


if __name__ == "__main__":
    init_database()