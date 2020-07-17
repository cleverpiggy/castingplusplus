import os, sys

def _test_db_url_and_name():
    db_url = os.environ['DATABASE_URL']
    parts = db_url.split('/')
    test_db_name = 'casting__test__db'
    parts[-1] = test_db_name
    return '/'.join(parts), test_db_name

TEST_DB_URL, TEST_DB_NAME = _test_db_url_and_name()


def main():
    print({'url': TEST_DB_URL, 'name': TEST_DB_NAME}[sys.argv[1]])

if __name__ == '__main__':
    main()
