# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- **Run Flask server**: `flask run` or `python run.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Database migrations**: 
  - Create migration: `flask db migrate -m "migration message"`
  - Apply migrations: `flask db upgrade`
- **Frontend development**:
  - Start React dev server: `cd frontend && npm start`
  - Build React for production: `cd frontend && npm run build`
  - Copy build to Flask: `cd frontend && ./copy_build_to_flask.sh`

## Code Style Guidelines
- **Imports**: Group in order: standard library, Flask/extensions, local modules
- **Formatting**: 4-space indentation, 120-char line length
- **Functions**: Use descriptive names, document with docstrings for complex logic
- **Error handling**: Use try/except with specific exceptions
- **Routes**: Group by functionality in blueprint files
- **Models**: Define relationships explicitly with backref
- **Frontend**: Use React functional components with Tailwind CSS
- **Type annotations**: Not strictly required but encouraged for complex functions
- **Variable naming**: snake_case for Python, camelCase for JavaScript

## Architecture
- Flask backend with blueprint structure (auth, planner)
- SQLAlchemy ORM for database models
- React frontend with Tailwind CSS
- Hybrid serving: Flask serves React build in production