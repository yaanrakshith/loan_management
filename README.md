 Loan Management System APP  
 API Endpoints
Authentication
- POST /api/auth/register/ - Register a new user with OTP verification.
- POST /api/auth/login/ - Login and receive a JWT token.
- POST /api/auth/resend-otp/ - Resend OTP for verification.
- POST /api/auth/verify-otp/ - Verify OTP to activate the account.
- POST /api/auth/refresh/ - Refresh JWT token.
- GET /api/auth/profile/ - Get user profile details.

 Loan 
- POST /api/loans/ - Apply for a loan.
- GET /api/loans/ - List all loans.
- GET /api/loans/{loan_id}/ - Get details of a specific loan.
- POST /api/loans/{loan_id}/foreclose/ - Foreclose a loan before tenure completion.
- POST /api/loans/{loan_id}/payment/ - Make a loan payment.


 Setup Guide
# Deploying Django on Render

# Prerequisites
Ensure you have the following before deploying your Django project on Render:
- A Django project in a GitHub repository.
- A Render account (sign up at Render's official website).
- PostgreSQL database configured on Render.

---

 Step 1: Prepare Your Django Project
## 1. Push Your Django Project to GitHub
Ensure your Django project is under version control and pushed to a GitHub repository.

### 2. Update Project Settings for PostgreSQL
Modify the database settings to use PostgreSQL with environment variables from Render.

### 3. Install Necessary Dependencies
Ensure required dependencies like Gunicorn, PostgreSQL adapter, and database URL handler are installed and listed in the requirements file.

### 4. Add a Deployment Process File
Create a process file that instructs Render on how to run the Django application.

### 5. Configure Allowed Hosts
Initially, allow all hosts for testing. Later, update it with the Render domain to enhance security.

### 6. Use Environment Variables for Security
Configure sensitive settings using environment variables instead of hardcoding them. Store values such as the secret key, debug mode, and database credentials securely in Render’s environment settings.

---

 Step 2: Set Up a PostgreSQL Database on Render
1. Log in to the Render dashboard.
2. Create a new PostgreSQL database.
3. Select a suitable plan (use the free tier for development if available).
4. After the database is created, copy the database URL.
5. Store this URL as an environment variable in the Render settings.

---

 Step 3: Deploy Django on Render
1. Go to the Render dashboard and create a new web service.
2. Connect the repository and select the Django project from GitHub.
3. Define the build command to install dependencies and apply migrations.
4. Set the start command to run the web application.
5. Add necessary environment variables, including the secret key, debug mode, and database URL.
6. Deploy the application.

---

 Step 4: Apply Migrations 
1. Run Django migrations to set up the database schema.
2. Configure static files storage for production use.
3. Collect and store static files appropriately.

---

 Step 5: Test and Secure Deployment
1. Open the deployed URL to verify the application is running correctly.
2. Restrict allowed hosts by updating the configuration with the Render domain.
3. Disable debug mode for production use.
4. Implement HTTPS enforcement and apply necessary security configurations.



Testing Instructions
- Use Postman collection to test all API endpoints.
- Validate authentication and loan operations.
- Verify response formats and error handling.


