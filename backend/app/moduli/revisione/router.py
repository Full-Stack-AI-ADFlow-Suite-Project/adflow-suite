"""Endpoint del modulo revisione: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["revisione"])
