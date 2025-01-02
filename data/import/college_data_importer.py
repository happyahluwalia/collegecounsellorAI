import os
import sys
import pandas as pd
import logging
from datetime import datetime
import json
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import execute_values

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from models.database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CollegeDataImporter:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.db = Database()
        self.data = None
        self.skipped_records = []
        self.batch_size = 1000  # Number of records to insert at once

    def read_csv(self):
        """Read the CSV file into a pandas DataFrame with robust error handling"""
        try:
            logger.info(f"Reading CSV file: {self.csv_file}")

            # Define columns we need with their expected types
            dtype_dict = {
                'unitid': 'Int64',
                'institution name': str,
                'HD2023.Street address or post office box': str,
                'HD2023.City location of institution': str,
                'HD2023.ZIP code': str,
                'HD2023.State abbreviation': str,
                'HD2023.Control of institution': str,
                'HD2023.Sector of institution': str,
                'IC2023.Housing capacity': 'Int64',
                'IC2023.Typical housing charges for an academic year': 'float64',
                'IC2023.Typical food charge for academic year': 'float64',
                'IC2023mission.Mission statement': str,
                'IC2023.Undergraduate application fee': 'float64',
                'HD2023.Financial aid office web address': str,
                'HD2023.Admissions office web address': str,
                'HD2023.Online application web address': str,
                'HD2023.Net price calculator web address': str
            }

            self.data = pd.read_csv(
                self.csv_file,
                dtype=dtype_dict,
                na_values=['', 'nan', 'NULL', 'None', '#N/A'],
                keep_default_na=True,
                on_bad_lines='skip'
            )

            logger.info(f"Successfully read {len(self.data)} rows")

        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise

    def clean_data(self):
        """Clean and prepare the data for import"""
        try:
            logger.info("Cleaning data...")

            # Save records with NA values in critical fields to skipped_records
            critical_fields = [
                'unitid', 'institution name', 'HD2023.City location of institution',
                'HD2023.State abbreviation'
            ]

            # Identify rows with NA values in critical fields
            na_mask = self.data[critical_fields].isna().any(axis=1)
            self.skipped_records = self.data[na_mask].copy()
            self.data = self.data[~na_mask].copy()

            # Save skipped records to CSV
            if not self.skipped_records.empty:
                skipped_file = self.csv_file.replace('.csv', '_skipped.csv')
                self.skipped_records.to_csv(skipped_file, index=False)
                logger.info(f"Saved {len(self.skipped_records)} skipped records to {skipped_file}")

            # Convert all remaining NaN values to None/NULL
            for col in self.data.columns:
                # Convert NaN to None
                mask = self.data[col].isna()
                self.data.loc[mask, col] = None

                # Handle numeric columns specially
                if col in ['IC2023.Housing capacity', 'IC2023.Typical housing charges for an academic year',
                          'IC2023.Typical food charge for academic year', 'IC2023.Undergraduate application fee']:
                    self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                    self.data[col] = self.data[col].where(pd.notnull(self.data[col]), None)

            logger.info(f"Data cleaning completed. {len(self.data)} records ready for import")

        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            raise

    def import_institutions(self):
        """Import data into the institutions table using batch processing"""
        try:
            logger.info("Importing institutions data...")
            successful_imports = 0
            failed_imports = 0

            # Convert DataFrame to list of tuples for batch insert
            values = []
            for idx, row in self.data.iterrows():
                try:
                    # Convert pandas values to Python native types
                    record = (
                        int(row['unitid']) if pd.notnull(row['unitid']) else None,
                        str(row['institution name']) if pd.notnull(row['institution name']) else None,
                        str(row['HD2023.Street address or post office box']) if pd.notnull(row['HD2023.Street address or post office box']) else None,
                        str(row['HD2023.City location of institution']) if pd.notnull(row['HD2023.City location of institution']) else None,
                        str(row['HD2023.ZIP code']) if pd.notnull(row['HD2023.ZIP code']) else None,
                        str(row['HD2023.State abbreviation']) if pd.notnull(row['HD2023.State abbreviation']) else None,
                        str(row['HD2023.Control of institution']) if pd.notnull(row['HD2023.Control of institution']) else None,
                        str(row['HD2023.Sector of institution']) if pd.notnull(row['HD2023.Sector of institution']) else None,
                        int(row['IC2023.Housing capacity']) if pd.notnull(row['IC2023.Housing capacity']) else None,
                        float(row['IC2023.Typical housing charges for an academic year']) if pd.notnull(row['IC2023.Typical housing charges for an academic year']) else None,
                        float(row['IC2023.Typical food charge for academic year']) if pd.notnull(row['IC2023.Typical food charge for academic year']) else None,
                        str(row['IC2023mission.Mission statement']) if pd.notnull(row['IC2023mission.Mission statement']) else None,
                        float(row['IC2023.Undergraduate application fee']) if pd.notnull(row['IC2023.Undergraduate application fee']) else None,
                        str(row['HD2023.Financial aid office web address']) if pd.notnull(row['HD2023.Financial aid office web address']) else None,
                        str(row['HD2023.Admissions office web address']) if pd.notnull(row['HD2023.Admissions office web address']) else None,
                        str(row['HD2023.Online application web address']) if pd.notnull(row['HD2023.Online application web address']) else None,
                        str(row['HD2023.Net price calculator web address']) if pd.notnull(row['HD2023.Net price calculator web address']) else None,
                    )
                    values.append(record)
                except Exception as e:
                    logger.error(f"Error preparing record at index {idx}: {str(e)}")
                    failed_imports += 1
                    continue

            # Process in batches
            for i in range(0, len(values), self.batch_size):
                batch = values[i:i + self.batch_size]
                try:
                    with self.db.conn.cursor() as cur:
                        execute_values(
                            cur,
                            """
                            INSERT INTO institutions (
                                unitid, institution_name, street_address, city,
                                zip_code, state_abbreviation, control_of_institution,
                                sector_of_institution, housing_capacity, typical_housing_charge,
                                typical_food_charge, mission_statement, undergraduate_application_fee,
                                financial_aid_office_url, admissions_office_url,
                                online_application_url, net_price_calculator_url
                            ) VALUES %s
                            ON CONFLICT (unitid) DO UPDATE SET
                                institution_name = EXCLUDED.institution_name,
                                street_address = EXCLUDED.street_address,
                                city = EXCLUDED.city,
                                zip_code = EXCLUDED.zip_code,
                                state_abbreviation = EXCLUDED.state_abbreviation,
                                control_of_institution = EXCLUDED.control_of_institution,
                                sector_of_institution = EXCLUDED.sector_of_institution,
                                housing_capacity = EXCLUDED.housing_capacity,
                                typical_housing_charge = EXCLUDED.typical_housing_charge,
                                typical_food_charge = EXCLUDED.typical_food_charge,
                                mission_statement = EXCLUDED.mission_statement,
                                undergraduate_application_fee = EXCLUDED.undergraduate_application_fee,
                                financial_aid_office_url = EXCLUDED.financial_aid_office_url,
                                admissions_office_url = EXCLUDED.admissions_office_url,
                                online_application_url = EXCLUDED.online_application_url,
                                net_price_calculator_url = EXCLUDED.net_price_calculator_url
                            """,
                            batch
                        )
                    self.db.conn.commit()
                    successful_imports += len(batch)
                    logger.info(f"Successfully imported batch of {len(batch)} records")
                except Exception as e:
                    self.db.conn.rollback()
                    logger.error(f"Error importing batch: {str(e)}")
                    failed_imports += len(batch)
                    continue

            logger.info(f"Import completed: {successful_imports} records imported successfully, "
                       f"{failed_imports} records failed, "
                       f"{len(self.skipped_records)} records skipped due to NA values")
        except Exception as e:
            logger.error(f"Error importing institutions data: {str(e)}")
            raise

    def import_all(self):
        """Run the complete import process"""
        try:
            logger.info("Starting full import process...")
            self.read_csv()
            self.clean_data()
            self.import_institutions()
            logger.info("Full import process completed successfully")
        except Exception as e:
            logger.error(f"Error during import process: {str(e)}")
            raise

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "All_college_export.csv")
    importer = CollegeDataImporter(csv_file)
    importer.import_all()