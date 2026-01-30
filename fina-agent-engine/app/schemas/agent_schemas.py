from pydantic import BaseModel, Field


class PortfolioSchema(BaseModel):
    """Schema for portfolio retrieval requests."""
    
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The unique ID of the user. Default to 'user123' if not specified."
    )


class SearchSchema(BaseModel):
    """Schema for document search requests."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The specific financial question or topic to search in the PDF documents."
    )
