if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "    Created .venv"
else
    echo "    .venv already exists, skipping creation"
fi

source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet faker mysql-connector-python

docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/load.sql"
docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/article57_load.sql"
python ./init/generate_data.py
docker compose exec mariadb bash -c "mariadb -uroot -pyour_password ygeiopolis  < /var/lib/mysql-files/generated_data.sql"