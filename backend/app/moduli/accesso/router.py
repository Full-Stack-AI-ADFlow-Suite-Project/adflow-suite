"""Endpoint del modulo accesso: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["accesso"])
