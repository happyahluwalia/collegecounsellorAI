-- This file stores the database schema required for managing college metadata.

-- Institution Table
-- Stores the basic details about institutions, including name, address, and control information.

CREATE TABLE institutions (
    unitid INT PRIMARY KEY,  -- Unique identifier for the institution
    institution_name VARCHAR(255),  -- Name of the institution
    street_address VARCHAR(255),  -- Street address of the institution
    city VARCHAR(100),  -- City location of the institution
    zip_code VARCHAR(20),  -- ZIP code of the institution
    state_abbreviation CHAR(2),  -- State abbreviation (e.g., CA, NY)
    control_of_institution VARCHAR(50),  -- Control type: Public, Private Not-for-Profit, Private For-Profit. 1	Public	2	Private not-for-profit		3	Private for-profit		-3	{Not available}
    sector_of_institution VARCHAR(50),  -- Sector classification (e.g., degree-granting, 2-year)
    housing_capacity INT,  -- Total capacity of student housing
    typical_housing_charge DECIMAL(10, 2),  -- Typical charge for student housing per academic year
    typical_food_charge DECIMAL(10, 2),  -- Typical charge for food per academic year
    mission_statement TEXT,  -- Mission statement of the institution
    undergraduate_application_fee DECIMAL(10, 2),  -- Fee for undergraduate applications
    financial_aid_office_url VARCHAR(255),  -- URL for the financial aid office
    admissions_office_url VARCHAR(255),  -- URL for the admissions office
    online_application_url VARCHAR(255),  -- URL for online applications
    net_price_calculator_url VARCHAR(255),  -- URL for the net price calculator
    PRIMARY KEY (unitid)
);

-- Admissions and Applications Table
-- Stores information related to admissions criteria and statistics.

CREATE TABLE admissions_applications (
    unitid INT REFERENCES institutions(unitid),  -- Foreign key to institutions table
    year INT,  -- Academic year
    secondary_school_GPA INT CHECK (secondary_school_GPA IN (1, 3, 5, -1, -2)),  
    -- Secondary school GPA requirement (1: Required, 5: Optional, 3: Not considered, -1: Not reported, -2: Not applicable)
    recommendations INT CHECK (recommendations IN (1, 5, 3, -1, -2)),  
    -- Recommendation letters requirement (1: Required, 5: Optional, 3: Not considered, -1: Not reported, -2: Not applicable)
    personal_statement_essay BOOLEAN,  -- Is a personal statement or essay required?
    admission_test_scores BOOLEAN,  -- Are standardized test scores required?
    applicants_total INT,  -- Total number of applicants
    applicants_men INT,  -- Total number of male applicants
    applicants_women INT,  -- Total number of female applicants
    admissions_total INT,  -- Total number of admissions
    admissions_men INT,  -- Total number of male admissions
    admissions_women INT,  -- Total number of female admissions
    sat_ebrw_75th_percentile INT,  -- 75th percentile SAT Evidence-Based Reading and Writing score
    sat_math_75th_percentile INT,  -- 75th percentile SAT Math score
    PRIMARY KEY (unitid, year)
);

-- Financial Aid Table
-- Stores financial aid data for students.

CREATE TABLE financial_aid (
    unitid INT REFERENCES institutions(unitid),  -- Foreign key to institutions table
    year INT,  -- Academic year
    percent_aided_fed_state_local_institution DECIMAL(5, 2),  
    -- Percentage of full-time, first-time undergraduates awarded any grant aid
    average_net_price DECIMAL(10, 2),  -- Average net price for students awarded grants or scholarships
    PRIMARY KEY (unitid, year)
);

-- Tuition and Fees Table
-- Stores tuition and fee details for in-district, in-state, and out-of-state students.

CREATE TABLE tuition_fees (
    unitid INT REFERENCES institutions(unitid),  -- Foreign key to institutions table
    year INT,  -- Academic year
    tuition_fees DECIMAL(10, 2),  -- Total tuition and fees for the academic year
    total_price_in_district_on_campus DECIMAL(10, 2),  -- Total price for in-district students living on campus
    total_price_in_state_on_campus DECIMAL(10, 2),  -- Total price for in-state students living on campus
    total_price_out_state_on_campus DECIMAL(10, 2),  -- Total price for out-of-state students living on campus
    total_price_in_district_off_campus DECIMAL(10, 2),  -- Total price for in-district students living off campus
    total_price_in_state_off_campus DECIMAL(10, 2),  -- Total price for in-state students living off campus
    total_price_out_state_off_campus DECIMAL(10, 2),  -- Total price for out-of-state students living off campus
    PRIMARY KEY (unitid, year)
);

-- Admissions Yield Table
-- Stores admissions yield data, including total yield and yield by demographics.

CREATE TABLE admissions_yield (
    unitid INT REFERENCES institutions(unitid),  -- Foreign key to institutions table
    year INT,  -- Academic year
    yield_total DECIMAL(5, 2),  -- Overall admissions yield (percentage)
    yield_men DECIMAL(5, 2),  -- Admissions yield for men (percentage)
    yield_women DECIMAL(5, 2),  -- Admissions yield for women (percentage)
    yield_full_time DECIMAL(5, 2),  -- Yield for full-time students (percentage)
    yield_full_time_men DECIMAL(5, 2),  -- Yield for full-time male students (percentage)
    yield_full_time_women DECIMAL(5, 2),  -- Yield for full-time female students (percentage)
    yield_part_time DECIMAL(5, 2),  -- Yield for part-time students (percentage)
    yield_part_time_men DECIMAL(5, 2),  -- Yield for part-time male students (percentage)
    yield_part_time_women DECIMAL(5, 2),  -- Yield for part-time female students (percentage)
    PRIMARY KEY (unitid, year)
);

-- Institution Characteristics Table
-- Stores characteristics like size category and degree-granting status.

CREATE TABLE institution_characteristics (
    unitid INT REFERENCES institutions(unitid),  -- Foreign key to institutions table
    year INT,  -- Academic year
    institution_size_category INT CHECK (institution_size_category IN (1, 2, 3, 4, 5, -1, -2)),  
    -- Size category (1: <1000, 2: 1000-4999, ..., 5: >20000, -1: Not reported, -2: Not applicable)
    degree_granting_status BOOLEAN,  -- Is the institution degree-granting?
    historically_black_college BOOLEAN,  -- Is the institution a Historically Black College?
    tribal_college BOOLEAN,  -- Is the institution a Tribal College?
    urban_centric_locale VARCHAR(50),  -- Urban-centric locale classification
    postsecondary_title_iv_indicator BOOLEAN,  -- Eligible for Title IV federal student aid programs
    institutional_category VARCHAR(100),  -- Broad institutional category
    PRIMARY KEY (unitid, year)
);
