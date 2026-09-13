#!/bin/sh
set -eu
: "${WIKI_DB_PASSWORD:?WIKI_DB_PASSWORD must be set}"
psql --variable=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=wiki_user=wiki_alien \
  --set=wiki_password="$WIKI_DB_PASSWORD" \
  --set=wiki_db=wiki_alien <<'SQL'
CREATE ROLE :"wiki_user"
  LOGIN
  PASSWORD :'wiki_password'
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOINHERIT;
CREATE DATABASE :"wiki_db"
  OWNER :"wiki_user"
  ENCODING 'UTF8';
SQL