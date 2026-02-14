from database import get_database_manager


if __name__ == "__main__":
    get_database_manager().init_db()
    print("Database initialized successfully.")
