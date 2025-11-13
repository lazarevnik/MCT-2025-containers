#!/bin/bash
echo "Надо ждать...."
until pg_isready - h db -U postgres; do
	sleep 1
done
echo "Инициализируем базу данных"
psql -h db -U postgres -f /init.sql
