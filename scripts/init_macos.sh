#!/bin/bash

# Expense Tracker initialization script specifically for macOS

echo "Initializing Expense Tracker configuration on macOS..."

# Check for Homebrew and install if needed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. You may want to install it for package management."
    echo "Visit https://brew.sh for installation instructions."
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    # Use macOS specific random generator
    RANDOM_KEY=$(LC_CTYPE=C tr -dc 'a-f0-9' < /dev/urandom | head -c 48)
    cat > ".env" << EOL
SECRET_KEY=${RANDOM_KEY}
FLASK_ENV=development
FLASK_DEBUG=1
EOL
    echo ".env file created with a random secret key"
else
    echo ".env file already exists"
fi

# Create config.yaml if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml file..."
    cat > "config.yaml" << EOL
users:
  - id: '1'
    username: 'admin'
    password: 'voicemain123'  # Remember to change this default password
EOL
    echo "config.yaml file created with default admin user"
    echo "IMPORTANT: Please change the default admin password in config.yaml"
else
    echo "config.yaml file already exists"
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p "data"
    chmod 700 "data"  # More restrictive permissions for data security
    echo "Data directory created with secure permissions"
else
    echo "Data directory already exists"
fi

echo "Initialization complete!"
echo "You may now run 'python app.py' to start the application"