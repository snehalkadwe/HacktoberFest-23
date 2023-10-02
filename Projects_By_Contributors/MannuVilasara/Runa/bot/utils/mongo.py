import requests
import pymongo


def mongo():
    db = pymongo.MongoClient("mongodb://localhost:27017")
    runa = db["Runa"]
    users = runa["users"]
    return users


def servers():
    db = pymongo.MongoClient("mongodb://localhost:27017")
    runa = db["Runa"]
    servers = runa["servers"]
    return servers
