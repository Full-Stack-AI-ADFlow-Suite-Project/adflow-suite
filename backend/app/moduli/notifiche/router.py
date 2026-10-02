"""Endpoint del modulo notifiche: chiamano service.py, senza logica di business."""

from fastapi import APIRouter

router = APIRouter(tags=["notifiche"])
