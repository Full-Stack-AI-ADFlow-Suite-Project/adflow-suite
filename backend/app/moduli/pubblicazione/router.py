"""Endpoint del modulo pubblicazione: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["pubblicazione"])
