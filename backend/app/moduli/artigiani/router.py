"""Endpoint del modulo artigiani: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["artigiani"])
