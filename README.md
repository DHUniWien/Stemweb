# Stemweb

## A service for calculating phylogenetic trees of variant texts

This software was originally written at the Helsinki Institute for Information Technology, and has been maintained since 2019 by the Digital Humanities group at the University of Vienna.

A white paper that describes its API [can be found here](https://stemmaweb.net/?p=58).

### Setup with docker-compose

1. Download the contents of the `docker` directory - this includes a docker-compose file and a few setup files for the necessary services.

2. Choose a password for the MySQL stemweb user. Save this password in `docker/.env` like so:

    MYSQL_PASSW="ThisIsMyPassword"

3. From the `docker` directory, run the command `docker-compose up`. This will start the three containers mysql, redis, and stemweb_py27, and expose the latter to localhost on port 8000.
