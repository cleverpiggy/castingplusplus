# castingplusplus

My Udacity Full Stack nano degree capstone project.

Castingplusplus is an API ([read the docs](#API-Reference)) to simplify the orginization of actors, movies, and roles for a hypothetical casting company.  It provides endpoints for adding, removing, editing and searching for all resources.  It implements authentication with Auth0 and RBAC with 3 tiers of authorization.

Check out the live version at `https://castingplusplus.herokuapp.com/`

### Get it running

Requires Python 3.5 or higher.

1. Clone the [repository](https://github.com/cleverpiggy/castingplusplus.git) and cd into the castingplusplus directory.
2. Install the requirements (using a virtualenv is encouraged).

   `% pip install -r requirements.txt`
3. Start a postgresql database.  I'm sure my audience of one Sir/Madam Udacity Reviewer can manage.

   `% createdb castingdb`
4. Set your database url to an environment variable named DATABASE_URL.  For example:

   `% export DATABASE_URL='postgresql://localhost:5432/castingdb'`
5. Optionally run a script to populate the database with some silly samples.

   `% python populate_testdb.py $DATABASE_URL`
6. Set the app variable.

   `% export FLASK_APP=flaskr`
7. Run the flask app.

   `% flask run`

Now you're ready to use it at  `http://127.0.0.1:5000/`.

#### Run the tests

You'll need the jwts.  For the purposes of the project, the script `request_jwts.py` uses 3 dummy AUTH0 accounts to collect the jwts and save them to jwts.py.  (Not very secure so don't use this app in an actual casting agency :-)).
```
% python request_jwts.py
```

If you prefer, you can edit `jwts.py` by pasting in values of jwts for ASSISTANT, DIRECTOR, and PRODUCER inside string quotes.
```

/jwts.py

ASSISTANT='<assistant jwt goes here>'
DIRECTOR='<director jwt goes here>'
PRODUCER='<producer jwt goes here>'
EXPIRED='<leave alone>'
```

Then running the tests couldn't be simipler:
```
% pytest
```

# API Reference

To access any endpoint an authorization header of the format
`Authorization:Bearer {token}`
must be included, where {token} is a JWT representing the appropriate authorization level.  In the examples below, we will assume the variable AUTHORIZED_HEADER has been set accordingly.

Keep in mind the attributes of Actors, Movies, and Roles referenced below when posting, viewing, or editing.  The *id* attributes are internally generated and should never be supplied in posts or edits.

- [Authorization Summary](#Authorization-Summary)
- [Actors](#Actors)
    - [Viewing Actors](#Viewing-Actors)
    - [Posting Actors](#Posting-Actors)
    - [Editing Actors](#Editing-Actors)
- [Movies](#Movies)
    - [Viewing Movies](#Viewing-Movies)
    - [Posting Movies](#Posting-Movies)
    - [Editing Movies](#Editing-Movies)
- [Roles](#Roles)
    - [Viewing Roles](#Viewing-Roles)
    - [Posting Roles](#Posting-Roles)
    - [Editing Roles](#Editing-Roles)
- [Deleting](#Deleting)
- [Errors](#Errors)


#### Authorization Summary
The authorization role hierarchy is Producer > Director > Assistant.  Higher roles have all permissions of lower roles.

Method | URL | Authorization
------ | --- | -------------
GET    | /actors | Assistant
GET    | /movies | Assistant
GET    | /roles  | Assistant
GET    | /movie/:id | Assistant
POST   | /roles/:id | Director
POST   | /actor | Director
POST   | /actor/:id/role/:id | Director
POST   | /movie | Producer
PATCH  | /actor/:id | Director
PATCH  | /movie/:id | Director
PATCH  | /role/:id | Director
DELETE | /actor/:id | Director
DELETE | /movie/:id | Producer
DELETE | /role/:id | Director

[\(back to the top\)](#API-Reference)

## Actors

#### Actor Attributes
- **id** `integer`
    - Unique id for the actor.
- **name** `string`
    - The actor's name.
- **age** `integer`
    - The actor's age.
- **gender** `string`
    - One of [male, female, non]

[\(back to the top\)](#API-Reference)

#### Viewing Actors

The base URL returns the first page of actors.  Optional query string parameters can be added to filter the list, customize page length, or specify a page.

- Method: **GET**

- Base URL: **/actors**

- Authorization Level: **Assistant**

- URL Parameters:
    - **page** `integer`
        - Requested page number
    - **page_length** `integer`
        - Number of Actors per page.
    - **gender** `string`
        - Filters gender.  Available values: [male, female, non]
    - **age** `range`
        - Filters an inclusive age range.  The format is {low}-{high}.  For example 25-35

- Example:
    ```
    % curl -H $AUTHORIZED_HEADER 'http://127.0.0.1:5000/actors?page_length=3&age=20-30'
    ```
    Response
    ```
    {
      "actors": [
        {
          "age": 25,
          "gender": "female",
          "id": 10,
          "name": "Sally"
        },
        {
          "age": 22,
          "gender": "female",
          "id": 13,
          "name": "Bridge"
        },
        {
          "age": 28,
          "gender": "female",
          "id": 14,
          "name": "Selena"
        }
      ],
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Posting Actors
Must supply all Actor attributes.  Returns the values posted.

- Method: **POST**

- Base URL: **/actor**

- Authorization Level: **Director**

- JSON: **Required**

- Example:
    ```
    % curl \
    -X POST \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json' \
    -d '{"name": "Jason Lee", "age": 31, "gender":"male"}' \
    'http://127.0.0.1:5000/actor'
    ```
    Response
    ```
    {
      "actor": {
        "age": 31,
        "gender": "male",
        "id": 46,
        "name": "Jason Lee"
      },
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Editing Actors
Here you can supply any or all of the Actor's attributes to edit.  Returns the attributes of the edited Actor.

- Method: **PATCH**

- Base URL: **/actor/:id**

- Authorization Level: **Director**

- JSON: **Required**

- Example:
    ```
    % curl \
    -X PATCH \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json'
    -d '{"name": "Jason Lee II"}' \
    'http://127.0.0.1:5000/actor/46'
    ```
    Response
    ```
    {
      "actor": {
        "age": 31,
        "gender": "male",
        "id": 46,
        "name": "Jason Lee II"
      },
      "success": true
    }

    ```

[\(back to the top\)](#API-Reference)

## Movies

#### Movie Attributes
- **id** `integer`
    - Unique id for the movie.
- **title** `string`
    - The movie's title.
- **release_date** `date`
    - The projected release date.

[\(back to the top\)](#API-Reference)

#### Viewing Movies
*2 Endpoints*
1. The base URL returns the first page of movies.  This does not include the movies' roles.  For that use /movie/:id.  Optional query string parameters can be added to customize page length or specify a page.

- Method: **GET**

- Base URL: **/movies**

- Authorization Level: **Assistant**

- URL Parameters:
    - **page** `integer`
        - Requested page number
    - **page_length** `integer`
        - Number of Movies per page.

- Example
    ```
    % curl \
    -H $AUTHORIZED_HEADER \
    'http://127.0.0.1:5000/movies?page_length=2'
    ```
    Response
    ```
    {
      "movies": [
        {
          "id": 4,
          "release_date": "Sun, 28 Mar 2021 00:00:00 GMT",
          "title": "The End"
        },
        {
          "id": 5,
          "release_date": "Sat, 12 Dec 2020 00:00:00 GMT",
          "title": "Best Wishes"
        }
      ],
      "success": true
    }

    ```

[\(back to the top\)](#API-Reference)

2. This returns extended info for a movie, including a list of roles.

- Method: **GET**

- Base URL: **/movie/:id**

- Authorization Level: **Assistant**

- Example:
    ```
    % curl \
    -H $AUTHORIZED_HEADER \
    'http://127.0.0.1:5000/movie/4'
    ```
    Response
    ```
    {
      "movie": {
        "id": 4,
        "release_date": "Sun, 28 Mar 2021 00:00:00 GMT",
        "title": "The End"
      },
      "roles": [
        {
          "age": 55,
          "filled": false,
          "gender": "male",
          "id": 1,
          "movie_id": 4,
          "name": "The Butler"
        },
        {
          "age": 25,
          "filled": false,
          "gender": "female",
          "id": 2,
          "movie_id": 4,
          "name": "The Waitress"
        },
        {
          "age": 45,
          "filled": false,
          "gender": "male",
          "id": 3,
          "movie_id": 4,
          "name": "The Villain"
        }
      ],
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Posting Movies
You must supply all Movie attributes.  Returns the values posted.

- Method: **POST**

- Base URL: **/movie**

- Authorization Level: **Producer**

- JSON: **Required**

- Example:
    ```
    % curl \
    -X POST \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json' \
    -d '{"title": "The Dog Comes Home", "release_date": "Sept 30, 2020"}' \
    'http://127.0.0.1:5000/movie'
    ```
    Response
    ```
    {
      "movie": {
        "id": 7,
        "release_date": "Wed, 30 Sep 2020 00:00:00 GMT",
        "title": "The Dog Comes Home"
      },
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Editing Movies
Here you can supply any or all of the Movie's attributes to edit. Returns the attributes of the edited Mole.

- Method: **PATCH**

- Base URL: **/movie/:id**

- Authorization Level: **Director**

- JSON: **Required**

- Example:
    ```
    % curl \
    -X PATCH \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json'
    -d '{"release_date": "Sept 30, 2021"}' \
    'http://127.0.0.1:5000/movie/7'
    ```
    Response
    ```
    {
      "movie": {
        "id": 7,
        "release_date": "Thu, 30 Sep 2021 00:00:00 GMT",
        "title": "The Dog Comes Home"
      },
      "success": true
    }

    ```

[\(back to the top\)](#API-Reference)

## Roles

#### Role Attributes
This has similar attributes to actor to allow easy matching.
- **id** `integer`
    - Unique id for the role.
- **name** `string`
    - The name of the character.
- **age** `integer`
    - The age of the character.
- **gender** `string`
    - One of [male, female, non]
- **filled** `bool`
    - Whether the role has been filled.
- **movie_id** `integer`
    - The id of the movie to which the role belongs.

[\(back to the top\)](#API-Reference)

#### Viewing Roles
The base URL returns the first page of roles.  Optional query string parameters can be added to customize page length, specify a page, or apply various filters.

- Method: **GET**

- Base URL: **/roles**

- Authorization Level: **Assistant**

- URL Parameters:
    - **page** `integer`
        - Requested page number
    - **page_length** `integer`
        - Number of Roles per page.
    - **gender** `string`
        - Filters gender.  Available values: [male, female, non]
    - **age** `range`
        - Filters an inclusive age range.  The format is {low}-{high}.  For example 25-35
    - **filled** `bool`
        - Filters whether the role has been filled [true, false]
    - **start_date** `date`
        - Return only roles for movies who's release date is after start_date.
    - **end_date** `date`
        - Return only roles for movies who's release date is before end_date.
- Example:
    ```
     % curl -H $AUTHORIZED_HEADER \
    'http://127.0.0.1:5000/roles?gender=female&age=20-30&end_date=12-31-2020&filled=false'
    ```
    Response
    ```
    {
      "roles": [
        {
          "age": 25,
          "filled": false,
          "gender": "female",
          "id": 5,
          "movie_id": 5,
          "name": "Ophelia"
        },
        {
          "age": 30,
          "filled": false,
          "gender": "female",
          "id": 8,
          "movie_id": 6,
          "name": "Lois Lane"
        }
      ],
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Posting Roles
Post a list of roles for one movie, appending to the current roles of that movie.  The id in the URL refers to the movie.  The 'filled' attribute is optional and defaults to false.  Returns the movie id and number of roles posted on success.

- Method: **POST**

- Base URL: **/roles/:id**

- Authorization Level: **Producer**

- JSON: **Required**

- Example:
    ```
    % curl \
    -X POST \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json' \
    -d '[{"name": "Sammy", "gender": "male", "age": 10},
    {"name": "Kendra", "gender": "female", "age": 9}]' \
    'http://127.0.0.1:5000/roles/7'
    ```
    Response
    ```
    {
      "movie": 7,
      "num_roles": 2,
      "success": true
    }
```

[\(back to the top\)](#API-Reference)

#### Editing Roles
Here you can supply any or all of the Role's attributes to edit.  Returns the attributes of the edited Role.

- Method: **PATCH**

- Base URL: **/role/:id**

- Authorization Level: **Director**

- JSON: **Required**

- Example:
    ```
     % curl \
    -H $AUTHORIZED_HEADER \
    -H 'Content-Type:application/json' \
    -d '{"name": "Junior"}' \
    -X PATCH \
    'http://127.0.0.1:5000/role/9'
    ```
    Response
    ```
    {
      "role": {
        "age": 10,
        "filled": false,
        "gender": "male",
        "id": 9,
        "movie_id": 7,
        "name": "Junior"
      },
      "success": true
    }
    ```

[\(back to the top\)](#API-Reference)

#### Deleting
The process of deleting is similar for Actors, Roles, and Movies.  Returns the attributes of the deleted item.

Method: DELETE

Base URLs | Authorization
--------- | ------------
/actor/:id | director
/role/:id  | director
/movie/:id | producer

Example:
```
% curl \
-X DELETE \
-H $AUTHORIZED_HEADER \
'http://127.0.0.1:5000/actor/46'
```
Response
```
{
  "actor": {
    "age": 31,
    "gender": "male",
    "id": 46,
    "name": "Jason Lee II"
  },
  "success": true
}
```

[\(back to the top\)](#API-Reference)

#### Errors
Erros will return json with an error description, name and status code.

Example:
```
% curl -H $AUTHORIZED_HEADER 'http://127.0.0.1:5000/actors?age=enlightenment'
```
Response
```
{
  "description": "Malformed age range",
  "name": "Unprocessable Entity",
  "status_code": 422,
  "success": false
}
```
```
% curl -H 'Authorization: Bearer just-sneaking-in' 'http://127.0.0.1:5000/actors'
```
Response
```
{
  "description": "Authorization malformed.",
  "name": "invalid_header",
  "status_code": 401,
  "success": false
}
```

[\(back to the top\)](#API-Reference)
