@echo off
REM 浮生十梦 Docker Deployment Script for Windows
REM This script helps deploy the application using Docker on Windows

setlocal enabledelayedexpansion

REM Colors for output (Windows doesn't support colors in batch easily, so we'll use echo)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Function to check if command exists
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker is not installed. Please install Docker first.
    exit /b 1
)

where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

echo %SUCCESS% Prerequisites check passed.

REM Setup environment file
if not exist .env (
    echo %INFO% Setting up environment file...
    copy .env.docker.example .env
    echo %WARNING% Please edit .env file with your configuration before continuing.
    echo %WARNING% At minimum, you need to set:
    echo %WARNING%   - OPENAI_API_KEY
    echo %WARNING%   - SECRET_KEY (generate with: openssl rand -hex 32)
    echo %WARNING%   - AUTH_USERS (username:password pairs)
    echo.
    pause
) else (
    echo %INFO% Environment file already exists.
)

REM Create necessary directories
echo %INFO% Creating necessary directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist nginx\ssl mkdir nginx\ssl
echo %SUCCESS% Directories created.

REM Parse command line arguments
set "COMMAND=%1"
set "OPTION=%2"

if "%COMMAND%"=="deploy" (
    call :deploy %OPTION%
) else if "%COMMAND%"=="stop" (
    call :stop
) else if "%COMMAND%"=="restart" (
    call :restart
) else if "%COMMAND%"=="logs" (
    call :logs
) else if "%COMMAND%"=="backup" (
    call :backup
) else if "%COMMAND%"=="update" (
    call :update
) else if "%COMMAND%"=="status" (
    call :status
) else if "%COMMAND%"=="help" (
    call :show_help
) else (
    echo %ERROR% Unknown command: %COMMAND%
    echo.
    call :show_help
    exit /b 1
)

goto :eof

:deploy
set "profile="
if "%1"=="--with-nginx" (
    set "profile=--profile nginx"
    echo %INFO% Deploying with Nginx reverse proxy...
) else (
    echo %INFO% Deploying application only...
)

echo %INFO% Building Docker images...
docker-compose build

echo %INFO% Starting services...
docker-compose %profile% up -d

echo %SUCCESS% Deployment completed!

REM Show status
docker-compose ps

echo.
echo %SUCCESS% Application is now running!
if "%1"=="--with-nginx" (
    echo %INFO% Access the application at: http://localhost
) else (
    echo %INFO% Access the application at: http://localhost:8000
)
goto :eof

:stop
echo %INFO% Stopping services...
docker-compose down
echo %SUCCESS% Services stopped.
goto :eof

:restart
call :stop
call :deploy
goto :eof

:logs
docker-compose logs -f
goto :eof

:backup
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "backup_dir=backups\%dt:~0,8%_%dt:~8,6%"
echo %INFO% Creating backup in %backup_dir%...
if not exist backups mkdir backups
if not exist %backup_dir% mkdir %backup_dir%
xcopy /E /I data %backup_dir%\data
copy .env %backup_dir%\
echo %SUCCESS% Backup created in %backup_dir%
goto :eof

:update
echo %INFO% Updating application...
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo %SUCCESS% Application updated.
goto :eof

:status
docker-compose ps
goto :eof

:show_help
echo 浮生十梦 Docker Deployment Script for Windows
echo.
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   deploy [--with-nginx]  Deploy the application
echo   stop                   Stop all services
echo   restart                Restart all services
echo   logs                   Show application logs
echo   backup                 Create a backup of data
echo   update                 Update and restart application
echo   status                 Show service status
echo   help                   Show this help message
echo.
echo Options:
echo   --with-nginx           Deploy with Nginx reverse proxy
echo.
echo Examples:
echo   %0 deploy              Deploy application only
echo   %0 deploy --with-nginx Deploy with Nginx
goto :eof
