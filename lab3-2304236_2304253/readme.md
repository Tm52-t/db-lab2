# Database Systems - Lab 3 (Problem 2 & Bonus)
**Team Members:**
- Taha Mohamed (ID: 2304236)
- Noor Elhawary (ID: 2304253)

## Project Overview
This project is a Flask-based web application integrated with a MySQL database (`library`) for managing authors and books, supporting CRUD operations and image upload functionality (Bonus).

## Setup & Execution Instructions

### 1. Database Setup
1. Open your MySQL client (e.g., MySQL Workbench).
2. Execute the DDL script to create the database and tables:
   - Run `problem2_DDL.sql`
3. Execute the DML script to populate initial seed data:
   - Run `problem2_DML.sql`

### 2. Running the Application
1. Open a terminal and navigate to the `website` directory.
2. Activate your virtual environment (if applicable):
   - Windows: `..\venv\Scripts\activate`
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt