# Legal Billable Hours Planner - Frontend

This is the React-based frontend for the Legal Billable Hours Planner app.

## Getting Started

1. **Install dependencies:**
   ```sh
   npm install
   ```

## Local Development

- Run the React frontend with:
  ```sh
  npm start
  ```
  This starts the dev server at [http://localhost:3000](http://localhost:3000), with API requests proxied to Flask at `localhost:5000` (see `proxy` in package.json).
- Run your Flask backend separately (e.g. `flask run`).
- Use your IDE's "Start" button or `npm start` for the frontend.

## Production Deployment (Flask Serves React)

1. **Build the React app:**
   ```sh
   npm run build
   ```
2. **Copy the build to Flask's static directory:**
   ```sh
   ./copy_build_to_flask.sh
   ```
   This copies the contents of `build/` into `../app/static/frontend/`.
3. **Flask serves the frontend:**
   - The Flask app is configured to serve all frontend routes and static assets from `/static/frontend`.
   - A catch-all route ensures React Router works for SPA navigation.

**Directory structure:**
```
/frontend             # React app source
/app/static/frontend  # Production build output (copied here)
/app/                 # Flask backend
```

**Example Flask setup:**
- See `/app/__init__.py` for the catch-all route that serves `index.html` for all non-API routes.

## Tech Stack
- React 18
- Tailwind CSS 3
- lucide-react icons

## Structure
- `src/DashboardRedesign.js`: Main dashboard UI (modular, easily extensible)
- `src/App.js`: App entrypoint
- `src/index.js` and `src/index.css`: Standard React/Tailwind setup

## Scripts

- `npm start` — Development mode (with proxy to Flask API)
- `npm run build` — Build production-ready static files
- `./copy_build_to_flask.sh` — Copy build output to Flask static directory for deployment

## Notes
- In production, you only need to run the Flask server; it will serve both the backend API and the frontend React app.
- For local development, keep React and Flask running separately.
- The catch-all route in Flask ensures deep links and React Router navigation work as expected.

## Backend API
This frontend is designed to communicate with your Flask backend via REST API endpoints. You can connect the dashboard to real data by fetching from your Flask server (e.g., using `fetch` or `axios`).

---

For further customization, add new pages/components in `src/` and update navigation as needed.
