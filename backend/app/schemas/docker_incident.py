from pydantic import BaseModel, Field


class DockerEvidence(BaseModel):
    container_id: str
    container_name: str
    image: str

    status: str
    restart_count: int = Field(ge=0)
    exit_code: int

    oom_killed: bool
    restart_policy: str

    started_at: str | None = None
    finished_at: str | None = None

    signals: list[str] = Field(default_factory=list)

    logs: str = ""