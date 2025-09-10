from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories.models import Conversation, ConversationStatus
import structlog

router = APIRouter()
log = structlog.get_logger()


class HandoffAction(BaseModel):
    action: str  # "human" | "bot"


@router.post("/conversations/{conversation_id}/handoff")
def set_handoff(conversation_id: int, body: HandoffAction):
    with SessionLocal() as db:  # type: Session
        convo = db.get(Conversation, conversation_id)
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if body.action == "human":
            convo.status = ConversationStatus.human_handoff
        elif body.action == "bot":
            convo.status = ConversationStatus.active_bot
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'human' or 'bot'.")
        db.add(convo)
        db.commit()
        log.info("handoff_changed", conversation_id=conversation_id, status=convo.status.value)
        return {"conversation_id": conversation_id, "status": convo.status.value}


class HumanSendMessage(BaseModel):
    conversation_id: int
    text: str


@router.post("/messages/send-human")
def send_message_as_human(body: HumanSendMessage):
    # Placeholder: neste momento apenas registra. Em seguida integraremos ao envio real.
    log.info(
        "human_message_send_requested",
        conversation_id=body.conversation_id,
        text=body.text,
    )
    return {"queued": True}
