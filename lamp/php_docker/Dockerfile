FROM php:8.4-fpm

# Installing dependencies for building the PHP modules
RUN apt update && \
  apt install -y --no-install-recommends zip libzip-dev libpng-dev libicu-dev libxml2-dev libpq-dev libonig-dev libcurl4-openssl-dev && \
  rm -rf /var/lib/apt/lists/*

# Installing additional PHP modules
RUN docker-php-ext-install mysqli pgsql pdo pdo_mysql pdo_pgsql gd zip intl xml mbstring curl opcache fileinfo bcmath soap

# Install Redis support via PECL
RUN pecl install redis \
  && docker-php-ext-enable redis

# Cleaning APT cache
RUN apt clean
