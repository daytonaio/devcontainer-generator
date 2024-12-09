# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DockerComposeService(BaseModel):
    image: Optional[str] = None
    build: Optional[Dict[str, Any]] = None
    volumes: Optional[List[str]] = None
    ports: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    depends_on: Optional[List[str]] = None

class DockerComposeModel(BaseModel):
    version: str = Field(..., description="Docker Compose file version")
    services: Dict[str, DockerComposeService] = Field(..., description="Services defined in the Docker Compose file")
    volumes: Optional[Dict[str, Any]] = Field(None, description="Named volumes defined in the Docker Compose file")
    networks: Optional[Dict[str, Any]] = Field(None, description="Networks defined in the Docker Compose file")

class DevContainerModel(BaseModel):
    name: str = Field(description="Name of the dev container")
    image: Optional[str] = Field(description="Docker image to use")
    dockerFile: Optional[str] = Field(description="Dockerfile to use")
    dockerComposeFile: Optional[str] = None
    service: Optional[str] = None
    workspaceFolder: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    forwardPorts: Optional[List[int]] = Field(
        description="Ports to forward from the container to the local machine"
    )
    customizations: Optional[dict] = Field(
        None, description="Tool-specific configuration"
    )
    settings: Optional[dict] = Field(
        None, description="VS Code settings to configure the development environment"
    )
    postCreateCommand: Optional[str] = Field(
        description="Command to run after creating the container"
    )
    postStartCommand: Optional[str] = None
    docker_compose: Optional[DockerComposeModel] = Field(None, description="Docker Compose configuration")