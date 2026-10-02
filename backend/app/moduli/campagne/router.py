"""Endpoint del modulo campagne: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["campagne"])
