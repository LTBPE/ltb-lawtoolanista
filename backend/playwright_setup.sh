#!/bin/bash
# Playwright browser installation script for Azure Functions Linux.
# Run once after deployment or set as the Function App startup command.
set -e
echo "Installing Playwright Chromium..."
playwright install chromium --with-deps 2>&1 || {
  echo "WARNING: playwright install failed (non-fatal). JS sites may not crawl."
}
echo "Playwright setup complete."
