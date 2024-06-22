#!/usr/bin/python3
from pydantic import BaseModel
from typing import Optional


class Object(BaseModel):
    id: str  # Object's ID.
    name: str  # Object's name.
    class_id: int  # The ID of an object class.
    child_ids: list  # An array of object's child objects IDs.
    child_link_ids: list  # An array of object's child links IDs.
    child_ref_ids: list  # An array of object's child references IDs.
    owner_id: Optional[str] = ""  # The ID of a user who owns the object.
    parent_id: list  # The IDs of an object's parents.
    discovery_id: Optional[str] = ""  # Object's discovery ID. See a detailed description below.
    properties: list  # An array of object's properties.
    client_data: Optional[str] = "" # Object's client data. See a detailed description below.
    state_id: int  # The ID of an object state.
    tags: list  # An array of object's tags.
    background: Optional[str] = ""  # Object's background image.
    created: int  # A timestamp when the object was created.
    geoposition: list  # Object's position on a map. It's specified as an array of two float numbers, where the first number is longitude, the second one is latitude.
    geopositionRadius: Optional[int] = ""  # The radius of an object's area displayed on a map.
    last_state_update: int  # A timestamp when object's state was last updated.
    manual_state: Optional[dict] = ""  # Object's manual state.
    operations: list  # An array of object's operations.
    updated: int  # A timestamp when the object was last updated.
    weight: int  # Object's weight.
