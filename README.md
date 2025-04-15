# Legal Billable Hours Planner

A web application to help legal professionals plan, track, and manage annual billable hour requirements.

## Features
- Personalized billable hour planning based on user input
- User authentication and secure data storage
- Calendar and dashboard views for progress tracking
- Tools for catch-up planning and workload adjustment

## Tech Stack
- Python 3.x, Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- SQLite (dev) / PostgreSQL (prod)
- HTML5, CSS3, Bootstrap, Jinja2

## Setup (Development)
1. Clone the repository and navigate to the project folder.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables (see `.env.example`).
5. Run the app:
   ```bash
   flask run
   ```

## Deployment
- Ready for deployment to Render, Fly.io, or Replit.
- Uses PostgreSQL for production.

## License
MIT License
