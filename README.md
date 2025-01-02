# College Compass 🎓

An AI-powered college admissions platform that helps students navigate the college application process with intelligent, data-driven guidance.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Setting Up Your Development Environment](#setting-up-your-development-environment)
4. [Running the Application](#running-the-application)
5. [Troubleshooting](#troubleshooting)

## Overview

College Compass combines multi-agent AI technology with robust data management to deliver:
- Personalized college recommendations
- Interactive college exploration
- AI-driven guidance system
- Application tracking
- Internship management

## Features

- 🤖 AI College Counselor
- 🏫 College Explorer
- 📊 Application Dashboard
- 🎯 Achievement System
- 📅 Timeline Management
- 💼 Internship Tracker

## Setting Up Your Development Environment

### Prerequisites

Don't worry! Most of these will be installed automatically. You just need:
1. A Replit account
2. OpenAI API key (for AI features)

### Step-by-Step Setup Guide

#### 1. Fork the Project
- Click the "Fork" button at the top of the Replit project
- This creates your own copy to work with

#### 2. Set Up Environment Variables
```bash
# The app will automatically ask for these when needed
OPENAI_API_KEY=your_api_key_here
```

#### 3. Database Setup
Good news! This is mostly automated. Just:
1. Click the "Run" button in Replit
2. The app will:
   - Create a PostgreSQL database
   - Set up all necessary tables
   - Import initial college data

If you want to do it manually:
1. Open the Shell in Replit
2. Run: `python3 data/import/college_data_importer.py`

#### 4. Install Dependencies
Just click "Run" - Replit will automatically:
- Install Python 3.11
- Install required packages:
  * streamlit
  * langchain
  * psycopg2-binary
  * and more...

### Running the Application

1. Click the "Run" button in Replit
2. Wait for the message: "You can now view your Streamlit app in your browser"
3. The app will open automatically in the Replit browser

That's it! You're running College Compass! 🎉

### Development Workflow

1. Make your changes
2. Click "Run" to restart the server
3. See your changes live!

### Database Management

The database structure is defined in `data/schema.sql`. To learn more:
1. Check `data/README.md` for database documentation
2. See `data/schema.sql` for complete schema

### Troubleshooting

#### Common Issues

1. **"Failed to connect to database" error**
   - Click "Run" again
   - The database takes a few seconds to start

2. **"ModuleNotFoundError" message**
   - Click "Run"
   - Replit will install missing packages

3. **Streamlit shows "Please wait..."**
   - Wait 30 seconds
   - The server is starting up

4. **"OpenAI API key not found" error**
   - Add your OpenAI API key in the secrets tab
   - The app will guide you through this

#### Still Having Issues?

1. Try these steps:
   - Click "Stop"
   - Wait 5 seconds
   - Click "Run"
   
2. If that doesn't help:
   - Open the Shell
   - Type: `python3 data/import/college_data_importer.py`
   - Click "Run"

3. Still stuck?
   - Check the logs in the Console
   - Look for red error messages
   - Follow the suggested fixes

### Getting Help

Need help? Try:
1. Asking our AI counselor in the chat
2. Checking the error messages
3. Reading the documentation in `data/README.md`

Remember: When in doubt, click "Run" - Replit will often fix things automatically! 😊

## Happy College Planning! 🎓
