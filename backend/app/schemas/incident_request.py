from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    service: str = Field(
        ...,
        description="Name of the affected service",
        examples=["payment-service"],
    )

    logs: str = Field(
        ...,
        description="Application or container logs",
        examples=["Connection refused to Redis"],
    )

    cpu: int = Field(
        ...,
        ge=0,
        le=100,
        description="CPU usage percentage",
        examples=[95],
    )

    memory: int = Field(
        ...,
        ge=0,
        le=100,
        description="Memory usage percentage",
        examples=[87],
    )