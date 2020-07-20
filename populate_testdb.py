from sys import argv
from dateutil.parser import parse
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from flaskr.models import Actor, Movie, Role, Booking, add_all, db
from flaskr import create_app


#name, age, gender
ACTORS =[
    'Tom,35,male',
    'Sally,25,female',
    'Jones,19,male',
    'Greg,56,male',
    'Bridge,22,female',
    'Selena,28,female',
    'Marge,61,female',
    'Pat,35,non'
]

#title release_date
MOVIES = [
    'The End,Mar 28 2021',
    'Best Wishes,Dec 12 2020',
    'This Sucks,Sept 20 2020'
]

def extract_movie(m):
    t, d = m.split(',')
    return [t, parse(d)]

# name age gender movie_id
ROLES = [
    'The Butler,55,male,0',
    'The Waitress,25,female,0',
    'The Villan,45,male,0',
    'Hamlet,28,male,1',
    'Ophelia,25,female,1',
    'Superman,30,male,2',
    'Lex Luthar,40,male,2',
    'Lois Lane,30,female,2'
]

def extract_role(r, movies):
    cols = r.split(',')
    cols[-1] = movies[int(cols[-1])].id
    return cols


def do_it(db_url, app=None):
    # engine = create_engine(db_url, echo=False)
    # session = sessionmaker(bind=engine)()
    if app is None:
        app = create_app({'DATABASE_URL': db_url})

    with app.app_context():
        session = db.session
        #first delete anything left in there
        for model in [Booking, Role, Actor, Movie]:
            session.query(model).delete()
        session.commit()

        columns = ['name', 'age', 'gender']
        actor_data = [dict(zip(columns, a.split(','))) for a in ACTORS]
        columns = ['title', 'release_date']
        movie_data = [dict(zip(columns, extract_movie(m))) for m in MOVIES]

        session.add_all(Actor(**d) for d in actor_data)
        session.add_all(Movie(**d) for d in movie_data)
        session.commit()
        movies = session.query(Movie).all()

        columns = ['name', 'age', 'gender', 'movie_id']
        role_data = [dict(zip(columns, extract_role(r, movies))) for r in ROLES]
        session.add_all(Role(**d) for d in role_data)
        session.commit()


def main():
    if len(argv) < 2:
        print ("Usage:  populate_test_db <database url>")
        return 1
    db_url = argv[1]
    do_it(db_url)
    print(db_url, 'populated')
    return 0

if __name__ == '__main__':
    main()
