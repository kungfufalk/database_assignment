docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/load.sql"
docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/article57_load.sql"
python ./init/generate_data.py
docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/generated_data.sql"