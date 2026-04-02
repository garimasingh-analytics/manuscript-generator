from __future__ import annotations

from bson import ObjectId


def oid(obj_id: str) -> ObjectId:
    return ObjectId(obj_id)


def str_id(doc: dict) -> dict:
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

