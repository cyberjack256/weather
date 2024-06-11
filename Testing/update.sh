#!/bin/bash

# Update the system
sudo yum update -y

# Install development tools and necessary libraries
sudo yum groupinstall "Development Tools" -y
sudo yum install bzip2-devel libffi-devel zlib-devel -y

# Download and install the latest OpenSSL if not already installed
cd /usr/src
if [ ! -d "openssl-1.1.1t" ]; then
  sudo wget https://www.openssl.org/source/openssl-1.1.1t.tar.gz
  sudo tar xzf openssl-1.1.1t.tar.gz
  sudo rm openssl-1.1.1t.tar.gz
fi

cd openssl-1.1.1t
sudo ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl
sudo make
sudo make install

# Update the system's OpenSSL library path
echo "/usr/local/openssl/lib" | sudo tee -a /etc/ld.so.conf.d/openssl-1.1.1t.conf
sudo ldconfig -v

# Remove existing OpenSSL symlink if it exists
sudo rm /usr/bin/openssl

# Create a new symlink for OpenSSL
sudo ln -s /usr/local/openssl/bin/openssl /usr/bin/openssl

# Verify OpenSSL installation
openssl version -a

# Download and install Python 3.9 if not already installed
cd /usr/src
if [ ! -d "Python-3.9.16" ]; then
  sudo wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
  sudo tar xzf Python-3.9.16.tgz
  sudo rm Python-3.9.16.tgz
fi

cd Python-3.9.16
sudo ./configure --enable-optimizations --with-openssl=/usr/local/openssl
sudo make altinstall

# Set Python 3.9 as the default version
sudo update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.9 1
sudo update-alternatives --set python3 /usr/local/bin/python3.9

# Verify Python installation
python3 --version
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"

# Upgrade pip and install required packages
python3 -m ensurepip
python3 -m pip install --upgrade pip
python3 -m pip install requests astral timezonefinder meteostat

# Clean up old packages and residual installs
sudo yum remove filebeat -y
sudo yum clean all

# Remove old Python versions
sudo rm -rf /usr/src/Python-3.7.16
sudo rm -rf /usr/src/Python-3.6.9

# Export SSL_CERT_FILE and SSL_CERT_DIR environment variables
export SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt
export SSL_CERT_DIR=/etc/pki/tls/certs

# Make the environment variable changes permanent
echo 'export SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt' >> ~/.bashrc
echo 'export SSL_CERT_DIR=/etc/pki/tls/certs' >> ~/.bashrc
source ~/.bashrc

echo "Deployment and cleanup completed successfully."