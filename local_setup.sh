#edit DATABASE_URL to reflect the local database you created
export DATABASE_URL='postgresql://cleverpiggy@localhost:5432/castingdb'
export FLASK_APP=flaskr
export FLASK_ENV=development

#there shouldn't be any need to edit these
export TEST_DB_URL='postgresql://localhost:5432/casting__test__db'
export TEST_DB_NAME='casting__test__db'
