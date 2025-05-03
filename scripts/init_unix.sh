#!/bin/bash

# Expense Tracker initialization script for Linux/macOS

echo "Initializing Expense Tracker configuration..."

# Create .env file if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "Creating .env file..."
    cat > "../.env" << EOL
SECRET_KEY=$(openssl rand -hex 24)
FLASK_ENV=development
FLASK_DEBUG=1
EOL
    echo ".env file created with a random secret key"
else
    echo ".env file already exists"
fi

# Create config.yaml if it doesn't exist
if [ ! -f "../config.yaml" ]; then
    echo "Creating config.yaml file..."
    cat > "../config.yaml" << EOL
users:
  - id: '1'
    username: 'admin'
    password: 'admin123'  # Remember to change this default password
EOL
    echo "config.yaml file created with default admin user"
    echo "IMPORTANT: Please change the default admin password in config.yaml"
else
    echo "config.yaml file already exists"
fi

# Create data directory if it doesn't exist
if [ ! -d "../data" ]; then
    echo "Creating data directory..."
    mkdir -p "../data"
    echo "Data directory created"
else
    echo "Data directory already exists"
fi

echo "Initialization complete!"
echo "You may now run 'python app.py' to start the application"