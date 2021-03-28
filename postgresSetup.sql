-- commands to setup database on clean Postges setup on a new machine or something like that
-- sudo -u postgres psql -f postgresSetup.sql
CREATE DATABASE ibit_task WITH ENCODING = 'UTF8';
CREATE USER ibit_task_admin WITH PASSWORD 'mewlDap=hispit9lCHiP';
ALTER USER ibit_task_admin CREATEDB;
ALTER ROLE ibit_task_admin SET client_encoding TO 'utf8';
ALTER ROLE ibit_task_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE ibit_task_admin SET timezone TO 'Europe/Moscow';
ALTER DATABASE ibit_task SET timezone TO 'Europe/Moscow';
GRANT ALL PRIVILEGES ON DATABASE ibit_task TO ibit_task_admin;
ALTER DATABASE ibit_task OWNER TO ibit_task_admin;