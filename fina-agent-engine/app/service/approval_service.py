"""ApprovalService - Business logic for approval operations.

Handles approval/rejection requests with governance validations,
segregation of duties, and audit trail creation.
"""

import datetime
from typing import Optional

from langchain_core.messages import HumanMessage

from app.core.config import VALID_SUPERVISORS
from app.core.exceptions import (
    AuthorizationError,
    ConflictOfInterestError,
    ThreadNotFoundError,
)
from app.core.logger import get_logger
from app.graph.builder import FinancialGraphManager
from app.schemas.approval_request import ApprovalRequest
from app.schemas.responses import ApprovalResponse

logger = get_logger("APPROVAL_SERVICE")


class ApprovalService:
    """Service for handling approval/rejection of financial recommendations."""
    
    def __init__(self, graph_manager: FinancialGraphManager):
        """Initialize ApprovalService.
        
        Args:
            graph_manager: Graph manager instance for state management
        """
        self.graph_manager = graph_manager
    
    def _validate_supervisor(self, supervisor_id: str) -> None:
        """Validate that supervisor is authorized.
        
        Args:
            supervisor_id: Supervisor's identifier
            
        Raises:
            AuthorizationError: If supervisor is not authorized
        """
        if supervisor_id not in VALID_SUPERVISORS:
            logger.warning(f"Unauthorized supervisor access: {supervisor_id}")
            raise AuthorizationError("Invalid Supervisor credentials")
    
    def _validate_segregation_of_duties(
        self,
        user_id: str,
        supervisor_id: str
    ) -> None:
        """Validate that creator and approver are different.
        
        Args:
            user_id: Request creator's ID
            supervisor_id: Supervisor's ID
            
        Raises:
            ConflictOfInterestError: If user and supervisor are the same
        """
        if user_id == supervisor_id:
            raise ConflictOfInterestError()
    
    def _validate_scope(
        self,
        user_id: str,
        stored_user_id: Optional[str]
    ) -> None:
        """Validate that request user matches thread owner.
        
        Args:
            user_id: Claimed user ID
            stored_user_id: Actual thread owner ID
            
        Raises:
            AuthorizationError: If user IDs don't match
        """
        if stored_user_id and stored_user_id != user_id:
            logger.error(f"Access violation: {user_id} vs {stored_user_id}")
            raise AuthorizationError("Security Violation: Scope mismatch")
    
    async def _check_idempotency(
        self,
        config: dict,
        thread_id: str
    ) -> Optional[ApprovalResponse]:
        """Check if thread was already processed.
        
        Args:
            config: Graph configuration
            thread_id: Thread identifier
            
        Returns:
            ApprovalResponse if already processed, None otherwise
        """
        graph = self.graph_manager.graph
        snapshot = await graph.aget_state(config)
        
        existing_decision = snapshot.values.get("final_decision")
        if existing_decision in ["approved", "rejected"]:
            return ApprovalResponse(
                status="already_processed",
                thread_id=thread_id,
                message=f"This thread was already finalized as: {existing_decision}"
            )
        return None
    
    def _build_audit_data(
        self,
        decision: str,
        supervisor_id: str,
        user_id: str
    ) -> dict:
        """Build audit trail data.
        
        Args:
            decision: "approved" or "rejected"
            supervisor_id: Supervisor who made decision
            user_id: User who requested
            
        Returns:
            Audit data dictionary
        """
        return {
            "final_decision": decision,
            "decision_by": supervisor_id,
            "requested_by": user_id,
            "decision_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    
    async def process_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Process an approval or rejection request.
        
        This method handles the complete approval workflow:
        1. Validates thread exists
        2. Validates supervisor authorization
        3. Validates segregation of duties
        4. Validates scope
        5. Checks idempotency
        6. Processes approval/rejection
        7. Creates audit trail
        
        Args:
            request: Approval request with decision
            
        Returns:
            ApprovalResponse with result
            
        Raises:
            ThreadNotFoundError: If thread doesn't exist
            AuthorizationError: If authorization fails
            ConflictOfInterestError: If segregation of duties violated
            HTTPException: If no pending review found
        """
        logger.info(f"Processing approval for thread {request.thread_id}")
        
        config = {"configurable": {"thread_id": request.thread_id}}
        graph = self.graph_manager.graph
        
        # Retrieve current state
        snapshot = await graph.aget_state(config)
        if not snapshot.values:
            raise ThreadNotFoundError(request.thread_id)
        
        # Governance validations
        self._validate_supervisor(request.supervisor_id)
        self._validate_segregation_of_duties(request.user_id, request.supervisor_id)
        
        # Scope validation
        stored_user_id = snapshot.values.get("user_id")
        self._validate_scope(request.user_id, stored_user_id)
        
        # Idempotency check
        idempotency_response = await self._check_idempotency(config, request.thread_id)
        if idempotency_response:
            return idempotency_response
        
        # Verify pending review state
        if not snapshot.next:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="No pending review found for this thread."
            )
        
        # Build audit data and seal decision
        decision = "approved" if request.approve else "rejected"
        audit_data = self._build_audit_data(decision, request.supervisor_id, request.user_id)
        await graph.aupdate_state(config, audit_data)
        
        if request.approve:
            return await self._process_approved(
                request, config, snapshot, audit_data
            )
        else:
            return await self._process_rejected(
                request, config, audit_data
            )
    
    async def _process_approved(
        self,
        request: ApprovalRequest,
        config: dict,
        snapshot,
        audit_data: dict
    ) -> ApprovalResponse:
        """Process approved request.
        
        Args:
            request: Approval request
            config: Graph configuration
            snapshot: Current state snapshot
            audit_data: Audit trail data
            
        Returns:
            ApprovalResponse with approved status
        """
        graph = self.graph_manager.graph
        
        # Handle supervisor edits
        if request.edited_response:
            current_messages = list(snapshot.values["messages"])
            current_messages[-1].content = request.edited_response
            await graph.aupdate_state(config, {"messages": current_messages})
            logger.info(f"Thread {request.thread_id} edited by Supervisor {request.supervisor_id}")
        
        # Resume flow to finalize
        final_state = await graph.ainvoke(None, config=config)
        
        return ApprovalResponse(
            status="approved",
            thread_id=request.thread_id,
            auditor=VALID_SUPERVISORS[request.supervisor_id],
            decision_at=audit_data["decision_at"],
            response=final_state["messages"][-1].content
        )
    
    async def _process_rejected(
        self,
        request: ApprovalRequest,
        config: dict,
        audit_data: dict
    ) -> ApprovalResponse:
        """Process rejected request.
        
        Args:
            request: Approval request
            config: Graph configuration
            audit_data: Audit trail data
            
        Returns:
            ApprovalResponse with rejected status
        """
        graph = self.graph_manager.graph
        
        # Inject rejection feedback
        feedback_message = HumanMessage(
            content="REJECTED BY SUPERVISOR: The previous recommendation is not authorized. Provide an alternative."
        )
        await graph.aupdate_state(config, {"messages": [feedback_message]})
        
        # Resume for agent to generate alternative
        final_state = await graph.ainvoke(None, config=config)
        
        return ApprovalResponse(
            status="rejected",
            thread_id=request.thread_id,
            auditor=VALID_SUPERVISORS[request.supervisor_id],
            decision_at=audit_data["decision_at"],
            message="Rejection feedback sent to agent.",
            new_agent_response=final_state["messages"][-1].content
        )
