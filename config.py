import os

DBUSER = os.environ["DBUSER"]# "root"
DBPASSWORD = os.environ["DBPASSWORD"] # "sQll0g1n"
DBADDR = os.environ.get("DBADDR", "127.0.0.1")
DBPORT = os.environ.get("DBPORT", "3306")
DATABASE = os.environ["DATABASE"]