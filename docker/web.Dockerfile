# Website: PHP 8.3 + Apache, with the PDO MySQL driver.
FROM php:8.3-apache
RUN docker-php-ext-install pdo_mysql \
 && sed -ri 's!AllowOverride None!AllowOverride All!g' /etc/apache2/apache2.conf \
 && printf 'display_errors=Off\nlog_errors=On\nupload_max_filesize=2M\npost_max_size=8M\n' > /usr/local/etc/php/conf.d/app.ini
# The site reads DB_* from the container environment (see docker-compose.yml).
