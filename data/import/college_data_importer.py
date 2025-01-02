import os
import sys
import pandas as pd
import logging
from datetime import datetime
import json

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

    def read_csv(self):
        """Read the CSV file into a pandas DataFrame with robust error handling"""
        try:
            logger.info(f"Reading CSV file: {self.csv_file}")
            self.data = pd.read_csv(
                self.csv_file,
                quoting=1,  # QUOTE_ALL
                escapechar='\\',
                on_bad_lines='warn',
                encoding='utf-8'
            )
            # Verify columns match expected schema
            required_cols = [
                'unitid', 'institution name', 'HD2023.Street address or post office box',
                'HD2023.City location of institution', 'HD2023.ZIP code',
                'HD2023.State abbreviation', 'HD2023.Control of institution'
            ]
            missing_cols = [col for col in required_cols if col not in self.data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            logger.info(f"Successfully read {len(self.data)} rows")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    def clean_data(self):
        """Clean and prepare the data for import"""
        try:
            logger.info("Cleaning data...")

            # Replace empty strings with None
            self.data = self.data.replace(r'^\s*$', None, regex=True)

            # Convert percentage strings to decimals
            for col in self.data.columns:
                if 'percent' in col.lower():
                    # Convert column to string first
                    str_series = self.data[col].astype(str)
                    # Remove '%' and convert to numeric, handling both string and numeric inputs
                    self.data[col] = pd.to_numeric(
                        str_series.str.rstrip('%').replace('nan', ''),
                        errors='coerce'
                    ) / 100

            # Convert currency strings to numeric
            for col in self.data.columns:
                if any(term in col.lower() for term in ['price', 'cost', 'fee', 'charge']):
                    # Convert to string first
                    str_series = self.data[col].astype(str)
                    # Remove currency symbols and commas, then convert to numeric
                    self.data[col] = pd.to_numeric(
                        str_series.replace('[\$,]', '', regex=True).replace('nan', ''),
                        errors='coerce'
                    )

            logger.info("Data cleaning completed")
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            raise

    def import_institutions(self):
        """Import data into the institutions table"""
        try:
            logger.info("Importing institutions data...")

            # Convert DataFrame to list of dictionaries for batch processing
            records = self.data.to_dict('records')

            for record in records:
                try:
                    self.db.execute("""
                        INSERT INTO institutions (
                            unitid, institution_name, street_address, city, 
                            zip_code, state_abbreviation, control_of_institution,
                            sector_of_institution, housing_capacity, typical_housing_charge,
                            typical_food_charge, mission_statement, undergraduate_application_fee,
                            financial_aid_office_url, admissions_office_url,
                            online_application_url, net_price_calculator_url
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
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
                    """, (
                        record['unitid'],
                        record['institution name'],
                        record['HD2023.Street address or post office box'],
                        record['HD2023.City location of institution'],
                        record['HD2023.ZIP code'],
                        record['HD2023.State abbreviation'],
                        record['HD2023.Control of institution'],
                        record['HD2023.Sector of institution'],
                        record['IC2023.Housing capacity'],
                        record['IC2023.Typical housing charges for an academic year'],
                        record['IC2023.Typical food charge for academic year'],
                        record['IC2023mission.Mission statement'],
                        record['IC2023.Undergraduate application fee'],
                        record['HD2023.Financial aid office web address'],
                        record['HD2023.Admissions office web address'],
                        record['HD2023.Online application web address'],
                        record['HD2023.Net price calculator web address']
                    ))
                except Exception as e:
                    logger.error(f"Error importing record for institution {record.get('unitid', 'unknown')}: {e}")
                    continue

            logger.info("Institutions data imported successfully")
        except Exception as e:
            logger.error(f"Error importing institutions data: {e}")
            raise

    def import_admissions_data(self):
        """Import data into the admissions_applications table"""
        try:
            logger.info("Importing admissions data...")
            current_year = datetime.now().year

            for _, record in self.data.iterrows():
                try:
                    self.db.execute("""
                        INSERT INTO admissions_applications (
                            unitid, year, secondary_school_GPA, recommendations,
                            personal_statement_essay, admission_test_scores,
                            applicants_total, applicants_men, applicants_women,
                            admissions_total, admissions_men, admissions_women,
                            sat_ebrw_75th_percentile, sat_math_75th_percentile
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (unitid, year) DO UPDATE SET
                            secondary_school_GPA = EXCLUDED.secondary_school_GPA,
                            recommendations = EXCLUDED.recommendations,
                            personal_statement_essay = EXCLUDED.personal_statement_essay,
                            admission_test_scores = EXCLUDED.admission_test_scores,
                            applicants_total = EXCLUDED.applicants_total,
                            applicants_men = EXCLUDED.applicants_men,
                            applicants_women = EXCLUDED.applicants_women,
                            admissions_total = EXCLUDED.admissions_total,
                            admissions_men = EXCLUDED.admissions_men,
                            admissions_women = EXCLUDED.admissions_women,
                            sat_ebrw_75th_percentile = EXCLUDED.sat_ebrw_75th_percentile,
                            sat_math_75th_percentile = EXCLUDED.sat_math_75th_percentile
                    """, (
                        record['unitid'], current_year,
                        1 if record['ADM2023.Secondary school GPA'] == 'Required' else 5 if record['ADM2023.Secondary school GPA'] == 'Optional' else 3,
                        1 if record['ADM2023.Recommendations'] == 'Required' else 5 if record['ADM2023.Recommendations'] == 'Optional' else 3,
                        record['ADM2023.Personal statement or essay'] == 'Required',
                        record['ADM2023.Admission test scores'] == 'Required',
                        record['ADM2023.Applicants total'],
                        record['ADM2023.Applicants men'],
                        record['ADM2023.Applicants women'],
                        record['ADM2023.Admissions total'],
                        record['ADM2023.Admissions men'],
                        record['ADM2023.Admissions women'],
                        record['ADM2023.SAT Evidence-Based Reading and Writing 75th percentile score'],
                        record['ADM2023.SAT Math 75th percentile score']
                    ))
                except Exception as e:
                    logger.error(f"Error importing admissions data for institution {record.get('unitid', 'unknown')}: {e}")
                    continue

            logger.info("Admissions data imported successfully")
        except Exception as e:
            logger.error(f"Error importing admissions data: {e}")
            raise

    def import_financial_aid(self):
        """Import data into the financial_aid table"""
        try:
            logger.info("Importing financial aid data...")
            current_year = datetime.now().year

            for _, record in self.data.iterrows():
                try:
                    self.db.execute("""
                        INSERT INTO financial_aid (
                            unitid, year, percent_aided_fed_state_local_institution,
                            average_net_price
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (unitid, year) DO UPDATE SET
                            percent_aided_fed_state_local_institution = EXCLUDED.percent_aided_fed_state_local_institution,
                            average_net_price = EXCLUDED.average_net_price
                    """, (
                        record['unitid'],
                        current_year,
                        record['SFA2223.Percent of full-time first-time undergraduates awarded federal, state, local or institutional grant aid'],
                        record['SFA2223.Average net price-students awarded grant or scholarship aid, 2022-23']
                    ))
                except Exception as e:
                    logger.error(f"Error importing financial aid data for institution {record.get('unitid', 'unknown')}: {e}")
                    continue

            logger.info("Financial aid data imported successfully")
        except Exception as e:
            logger.error(f"Error importing financial aid data: {e}")
            raise

    def import_all(self):
        """Run the complete import process"""
        try:
            logger.info("Starting full import process...")
            self.read_csv()
            self.clean_data()
            self.import_institutions()
            self.import_admissions_data()
            self.import_financial_aid()
            logger.info("Full import process completed successfully")
        except Exception as e:
            logger.error(f"Error during import process: {e}")
            raise

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "All_college_export.csv")
    importer = CollegeDataImporter(csv_file)
    importer.import_all()