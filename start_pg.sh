#!/bin/bash

# Start a standalone instance of postgresql

sudo mkdir /run/postgresql
sudo chown ark:ark /run/postgresql
pg_ctl start -D data
