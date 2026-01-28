from pydantic import BaseModel, Field

class PortfolioSchema(BaseModel):
    """Esquema para la consulta del portafolio privado."""
    user_id: str = Field(
        description="The unique ID of the user. Default to 'user123' if not specified."
    )

class SearchSchema(BaseModel):
    """Esquema para la búsqueda en documentos PDF."""
    query: str = Field(
        description="The specific financial question or topic to search in the PDF documents."
    )