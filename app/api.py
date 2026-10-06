from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import CreatePayloadResponse, PayloadCreateRequest, ReadPayloadResponse
from app.service import TransformationCacheService


def build_router(service: TransformationCacheService, get_db):
    router = APIRouter()

    def db_session():
        yield from get_db()

    @router.post(
        "/payload",
        response_model=CreatePayloadResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_payload(request: PayloadCreateRequest, session: Session = Depends(db_session)):
        try:
            request.validate_same_length()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        payload = service.create_payload(session, request.list_1, request.list_2)
        return CreatePayloadResponse(id=payload.id, message="Payload created")

    @router.get("/payload/{payload_id}", response_model=ReadPayloadResponse)
    def read_payload(payload_id: str, session: Session = Depends(db_session)):
        payload = service.get_payload(session, payload_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Payload not found")
        return ReadPayloadResponse(output=payload.output)

    return router
