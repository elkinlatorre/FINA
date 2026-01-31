import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.service.approval_service import ApprovalService
from app.schemas.approval_request import ApprovalRequest
from app.core.exceptions import AuthorizationError

@pytest.mark.asyncio
async def test_process_approval_unauthorized_supervisor():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    
    req = ApprovalRequest(
        thread_id="t1", user_id="u1", supervisor_id="INVALID", approve=True
    )
    
    # Mocking graph.aget_state to return a thread
    mock_graph = AsyncMock()
    mock_graph.aget_state.return_value = MagicMock(values={"user_id": "u1"})
    mock_manager.graph = mock_graph

    with pytest.raises(AuthorizationError) as exc:
        await service.process_approval(req)
    assert "Invalid Supervisor credentials" in str(exc.value)

@pytest.mark.asyncio
async def test_process_approval_success():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    
    # Needs valid supervisor ID from settings
    from app.core.settings import settings
    valid_sup = list(settings.VALID_SUPERVISORS.keys())[0]
    
    req = ApprovalRequest(
        thread_id="t1", user_id="u1", supervisor_id=valid_sup, approve=True
    )
    
    mock_graph = AsyncMock()
    # Snapshot values
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "u1", "messages": [MagicMock(content="old")]}
    mock_snapshot.next = ["gate"]
    mock_graph.aget_state.return_value = mock_snapshot
    
    # Mock update and invoke
    mock_graph.aupdate_state = AsyncMock()
    mock_graph.ainvoke.return_value = {"messages": [MagicMock(content="final response")]}
    
    mock_manager.graph = mock_graph
    
    response = await service.process_approval(req)
    assert response.status == "approved"
    assert response.response == "final response"

@pytest.mark.asyncio
async def test_process_approved_with_edit():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    val_sup = "SUP-9988"
    req = ApprovalRequest(
        thread_id="t1", user_id="u1", supervisor_id=val_sup, approve=True, edited_response="Edited"
    )
    
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    # Mocking message content that can be changed
    msg = MagicMock()
    mock_snapshot.values = {"user_id": "u1", "messages": [msg]}
    mock_snapshot.next = ["gate"]
    mock_graph.aget_state.return_value = mock_snapshot
    mock_graph.aupdate_state = AsyncMock()
    mock_graph.ainvoke.return_value = {"messages": [MagicMock(content="Final binary response")]}
    mock_manager.graph = mock_graph
    
    await service.process_approval(req)
    # Verify edit was applied
    assert msg.content == "Edited"
    assert mock_graph.aupdate_state.called

@pytest.mark.asyncio
async def test_process_approval_rejected():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    val_sup = "SUP-9988" # from settings
    req = ApprovalRequest(thread_id="t1", user_id="u1", supervisor_id=val_sup, approve=False)
    
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "u1", "messages": [MagicMock(content="old")]}
    mock_snapshot.next = ["gate"]
    mock_graph.aget_state.return_value = mock_snapshot
    mock_graph.ainvoke.return_value = {"messages": [MagicMock(content="rejected alternative")]}
    mock_manager.graph = mock_graph
    
    response = await service.process_approval(req)
    assert response.status == "rejected"
    assert response.new_agent_response == "rejected alternative"

@pytest.mark.asyncio
async def test_process_approval_already_processed():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    val_sup = "SUP-9988"
    req = ApprovalRequest(thread_id="t1", user_id="u1", supervisor_id=val_sup, approve=True)
    
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "u1", "final_decision": "approved"}
    mock_graph.aget_state.return_value = mock_snapshot
    mock_manager.graph = mock_graph
    
    response = await service.process_approval(req)
    assert response.status == "already_processed"

@pytest.mark.asyncio
async def test_process_approval_scope_mismatch():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    val_sup = "SUP-9988"
    req = ApprovalRequest(thread_id="t1", user_id="u1", supervisor_id=val_sup, approve=True)
    
    mock_graph = AsyncMock()
    # Stored user_id is different (u2)
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "u2"}
    mock_graph.aget_state.return_value = mock_snapshot
    mock_manager.graph = mock_graph
    
    from app.core.exceptions import AuthorizationError
    with pytest.raises(AuthorizationError) as exc:
        await service.process_approval(req)
    assert "Scope mismatch" in str(exc.value)

@pytest.mark.asyncio
async def test_process_approval_conflict_of_interest():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    # user_id same as supervisor_id (unlikely in real IDs but good for logic test)
    req = ApprovalRequest(thread_id="t1", user_id="SUP-9988", supervisor_id="SUP-9988", approve=True)
    
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "SUP-9988"}
    mock_graph.aget_state.return_value = mock_snapshot
    mock_manager.graph = mock_graph
    
    from app.core.exceptions import ConflictOfInterestError
    with pytest.raises(ConflictOfInterestError):
        await service.process_approval(req)

@pytest.mark.asyncio
async def test_process_approval_thread_not_found():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    req = ApprovalRequest(thread_id="none", user_id="u1", supervisor_id="SUP-9988", approve=True)
    
    mock_graph = AsyncMock()
    mock_graph.aget_state.return_value = MagicMock(values={})
    mock_manager.graph = mock_graph
    
    from app.core.exceptions import ThreadNotFoundError
    with pytest.raises(ThreadNotFoundError):
        await service.process_approval(req)

@pytest.mark.asyncio
async def test_process_approval_no_pending_review():
    mock_manager = MagicMock()
    service = ApprovalService(mock_manager)
    val_sup = "SUP-9988"
    req = ApprovalRequest(thread_id="t1", user_id="u1", supervisor_id=val_sup, approve=True)
    
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.values = {"user_id": "u1"}
    mock_snapshot.next = [] # NO PENDING REVIEW
    mock_graph.aget_state.return_value = mock_snapshot
    mock_manager.graph = mock_graph
    
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await service.process_approval(req)
    assert exc.value.status_code == 400
    assert "No pending review" in exc.value.detail
