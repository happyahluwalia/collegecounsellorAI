import logging
import pandas as pd
from models.database import Database

logger = logging.getLogger(__name__)

class CollegeDataImporter:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.db = Database()
        self.batch_size = 1000

    def import_all(self):
        """Import all college data from CSV"""
        try:
            logger.info("Starting full import process...")
            logger.info(f"Reading CSV file: {self.csv_file_path}")
            
            # Read CSV file
            df = pd.read_csv(self.csv_file_path)
            logger.info(f"Successfully read {len(df)} rows")

            # Clean data
            logger.info("Cleaning data...")
            df = self._clean_data(df)
            logger.info(f"Data cleaning completed. {len(df)} records ready for import")

            # Import data in batches
            logger.info("Importing institutions data...")
            failed_records = []
            skipped_records = []

            for i in range(0, len(df), self.batch_size):
                batch = df[i:i + self.batch_size]
                try:
                    self._import_batch(batch)
                    logger.info(f"Successfully imported batch of {len(batch)} records")
                except Exception as e:
                    logger.error(f"Error importing batch: {str(e)}")
                    failed_records.extend(batch.index.tolist())

            logger.info(
                f"Import completed: {len(df) - len(failed_records) - len(skipped_records)} "
                f"records imported successfully, {len(failed_records)} records failed, "
                f"{len(skipped_records)} records skipped due to NA values"
            )
            
            logger.info("Full import process completed successfully")
            return True

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return False

    def _clean_data(self, df):
        """Clean and prepare data for import"""
        # Add any necessary data cleaning steps here
        return df

    def _import_batch(self, batch):
        """Import a batch of records into the database"""
        values = []
        for _, row in batch.iterrows():
            values.append((
                row['name'] if 'name' in row else None,
                row['location'] if 'location' in row else None,
                row['description'] if 'description' in row else None,
                row['website'] if 'website' in row else None
            ))

        self.db.execute(
            """
            INSERT INTO institutions (name, location, description, website)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                location = EXCLUDED.location,
                description = EXCLUDED.description,
                website = EXCLUDED.website
            """,
            values,
            execute_many=True
        )
