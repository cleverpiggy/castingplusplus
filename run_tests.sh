# test whether postgres is running, avoiding 10 pages of error output
pg_isready
if [ $? -eq 0 ]
then
    source local_setup.sh
    dropdb --if-exists $TEST_DB_NAME
    createdb $TEST_DB_NAME
    # making this throw away app populates the tables
    python -c "from flaskr import create_app;create_app({'DATABASE_URL':\"$TEST_DB_URL\"})"
    python populate_testdb.py $TEST_DB_URL
    pytest $*
    dropdb $TEST_DB_NAME
else
    echo 'postgresql must be accepting connections for this to work'
fi
