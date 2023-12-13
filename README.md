# zephyr-python-server

## Development steps

### Setting up development environment

- Create and activate a python virtual environment
- Install dependencies using 

    `$ pip install -r requirements.txt`

- Change directory to `src` using 

    `$ cd src`

    The server should be executed from the `src` folder to avoid errors

- Generate gRPC files and database using:

    `$ ./setup.sh`

- Run the server:

    `$ python3 server.py`

### Making database schema changes:

- Create all the models in `models` directory. Use `User` model as reference.

- Once the necessary changes are made, create a new revision using:

    `$ alembic revision --autogenerate -m "<message>"`

    where `<message>` is similar to a commit message.

- To migrate the changes to database, run:

    `$ alembic upgrade head`