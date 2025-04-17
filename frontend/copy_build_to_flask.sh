#!/bin/bash
# Copies the React production build into the Flask static directory for deployment

FRONTEND_BUILD_DIR="$(dirname "$0")/build"
FLASK_STATIC_DIR="../app/static/frontend"

if [ ! -d "$FRONTEND_BUILD_DIR" ]; then
  echo "React build directory not found. Run 'npm run build' first."
  exit 1
fi

mkdir -p "$FLASK_STATIC_DIR"
cp -r "$FRONTEND_BUILD_DIR"/* "$FLASK_STATIC_DIR"/
echo "Copied React build to Flask static/frontend directory."
