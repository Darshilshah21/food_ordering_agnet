from fastapi import APIRouter, HTTPException
from backend.agent.agent import run_agent
from backend.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        response = run_agent(request.message, request.session_id)

        order_id = None
        marker = "ORDER_CREATED id="
        if marker in response:
            try:
                order_id = int(response.split(marker, 1)[1].split()[0])
            except (ValueError, IndexError):
                pass

        return ChatResponse(response=response, order_id=order_id)

    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=(
                "AI agent is temporarily unavailable. "
                "Check that Ollama is running and the configured model is installed. "
                f"Details: {type(exc).__name__}: {exc}"
            ),
        )
