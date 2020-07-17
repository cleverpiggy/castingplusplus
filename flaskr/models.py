from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (Column, String, Integer, DateTime,
                        CheckConstraint, ForeignKey, Boolean)

db = SQLAlchemy()

def setup_db(app, database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    # this line will be used in case of a test db not set up in migrate
    db.create_all()


def rollback():
    db.session.rollback()

def close_session():
    db.session.close()

def add_all(items):
    db.session.add_all(items)
    db.session.commit()


class BaseModel(db.Model):
    __abstract__ = True

    def add(self):
        db.session.add(self)
        db.session.commit()

    def format(self):
        # Not sure how robust this is.  It appears instance.__dict__
        # contains only attributes defined here and stuff starting with '_'.
        return {p: getattr(self, p) for p in self.viewable_properties}

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, mapping=None, **kwargs):
        if mapping is None:
            mapping = kwargs
        for k, v in mapping.items():
            setattr(self, k, v)
        db.session.commit()

    @classmethod
    def plural(cls):
        return cls.__tablename__ + 's'

    @classmethod
    def singular(cls):
        return cls.__tablename__


class Actor(BaseModel):
    __tablename__ = 'actor'
    viewable_properties = ['id', 'name', 'age', 'gender']

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, CheckConstraint('age > 0'), nullable=False)
    gender = Column(String(15),
                    CheckConstraint("gender in ('male', 'female', 'non')"),
                    nullable=False)
    bookings = db.relationship('Booking', backref='actor', lazy=True,
                               cascade='all, delete-orphan')


    def __repr__(self):
        return f'<Actor {self.id} {self.name}>'



class Movie(BaseModel):
    __tablename__ = 'movie'
    viewable_properties = ['id', 'title', 'release_date']

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    release_date = Column(DateTime, nullable=False)
    roles = db.relationship('Role', backref='movie', lazy=True,
                            cascade='all, delete-orphan')
    def __repr__(self):
        return f'<Move {self.id} {self.title}>'


# Roles represent roles in a movie.  Each movie has several.
class Role(BaseModel):
    __tablename__ = 'role'
    viewable_properties = ['id', 'name', 'age', 'gender', 'filled', 'movie_id']

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, CheckConstraint('age > 0'), nullable=False)
    gender = Column(String(15),
                    CheckConstraint("gender in ('male', 'female', 'non')"),
                    nullable=False)
    filled = Column(Boolean, nullable=False, default=False)
    movie_id = Column(Integer, ForeignKey('movie.id'), nullable=False)

    def __repr__(self):
        return f'<Role {self.id} {self.name}>'


# A Booking is where an actor is matched with a role.
class Booking(BaseModel):
    __tablename__ = 'booking'
    viewable_properties = ['id', 'actor_id', 'role_id']

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    actor_id = Column(Integer, ForeignKey('actor.id'), nullable=False)

    def __repr__(self):
        return f'<Booking {self.id} role({self.role_id}) actor({self.actor_id})>'
