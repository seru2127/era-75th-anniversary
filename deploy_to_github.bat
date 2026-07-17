@echo off
echo ========================================
echo Deploying to GitHub for Render.com
echo ========================================
echo.
echo Step 1: Initialize Git repository...
git init
git add .
git commit -m "Initial commit for Render deployment"
echo.
echo Step 2: Create repository on GitHub first!
echo Go to https://github.com/new and create a new repository.
echo Then run these commands:
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/era-registration.git
echo git push -u origin main
echo.
echo After pushing, go to https://render.com and deploy!
pause
