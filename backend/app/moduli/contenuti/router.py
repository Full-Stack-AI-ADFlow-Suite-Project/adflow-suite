"""Endpoint del modulo contenuti: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["contenuti"])
