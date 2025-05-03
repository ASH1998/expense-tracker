@echo off
setlocal EnableDelayedExpansion

echo Initializing Expense Tracker configuration...

:: Check if .env exists and create it if not
if not exist "..\\.env" (
    echo Creating .env file...
    
    :: Generate a random hexadecimal string for SECRET_KEY
    set "hex=0123456789ABCDEF"
    set "secret_key="
    for /L %%i in (1,1,48) do (
        set /a "rand=!random! %% 16"
        for %%j in (!rand!) do set "secret_key=!secret_key!!hex:~%%j,1!"
    )
    
    (
        echo SECRET_KEY=!secret_key!
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
    ) > "..\\.env"
    
    echo .env file created with a random secret key
) else (
    echo .env file already exists
)

:: Check if config.yaml exists and create it if not
if not exist "..\\config.yaml" (
    echo Creating config.yaml file...
    
    (
        echo users:
        echo   - id: '1'
        echo     username: 'admin'
        echo     password: 'admin123'  # Remember to change this default password
    ) > "..\\config.yaml"
    
    echo config.yaml file created with default admin user
    echo IMPORTANT: Please change the default admin password in config.yaml
) else (
    echo config.yaml file already exists
)

:: Check if data directory exists and create it if not
if not exist "..\\data" (
    echo Creating data directory...
    mkdir "..\\data"
    echo Data directory created
) else (
    echo data directory already exists
)

echo Initialization complete!
echo You may now run 'python app.py' to start the application

pause