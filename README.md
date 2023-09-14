# StemWeb - Stemmatological Algorithms Online

This is a project conceived in 2012 at the Complex Systems Computation Group at the Helsinki Institute of Information technology. This fork is a continuation and updating of the project carried out by the Digital Humanities Group at the University of Vienna.

## Running the service

Stemweb is a Python 3 / Django web app, using Celery for task queueing and with external dependencies on an SQL server (either ) and Redis. 

To run the service , first create a `.env` file according to the pattern found in `.env.example` in this directory, setting appropriate values for at least `STEMWEB_DBENGINE`, `STEMWEB_DBNAME`, `STEMWEB_DBUSER`, `STEMWEB_DBPASS`, and `STEMWEB_SECRET_KEY`. You can then start the service with the provided docker-compose file, or manually.

If you are using Docker, you can now run the command `docker compose up` in this directory. Three containers should start:

- A MySQL container, running on `mysql:3306` and not open to the outside
- A Redis container, running on `redis:6379` and not open to the outside
- A Stemweb server, running on `stemweb:8000` and mapped to localhost:8000

If you run the command `docker compose --profile testing up` instead, an additional container will start:

- A Stemweb testing client, running on `client:8001` and mapped to localhost:8001.

If you wish to run the service independently and not containerised, what passes for setup guidance can be found in the `Dockerfile` in this directory.

## Using the service

It should now be possible to make requests to Stemweb according to the [guidelines in the white paper](https://stemmaweb.net/?p=58).

If you are running the testing client (see above), you can make the following requests to see Stemweb in operation.

    curl -X POST http://localhost:8001/request/01_rhm
    curl -X POST http://localhost:8001/request/02_nj
    curl -X POST http://localhost:8001/request/03_nnet

will make requests to the Stemweb service using the respective test data in `client/requests`. These will return responses that look like:

    {"jobid": 1,"status": 1}

Eventually, a file `result-{jobid}-{date}.json` should appear in the `client/received` directory here, which is Stemweb's answer. This can also be called up with the command

    curl http://localhost:8001/query/{jobid}

