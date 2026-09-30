from app import app
import os

if __name__ == "__main__":
    # Make sure the database directory exists
    os.makedirs('data/db', exist_ok=True)

    # Run the data generation script if the database doesn't exist
    if not os.path.exists('data/db/supply_chain.sqlite'):
        print("Initializing database with sample data...")
        import data.generate_data
        import data.etl

    # Run the Flask application
    app.run(debug=True)