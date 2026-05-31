"""
Docker container management for isolated code execution.
"""

import docker
import os
from utils import logger
import shlex


def _is_custom_local_image(image_name: str) -> bool:
    """Heuristic: unqualified repository names are usually local custom images."""
    repository = image_name.split(":", 1)[0]
    return "/" not in repository and repository not in {"python", "gcc", "node", "ubuntu", "debian", "alpine"}

class DockerManager:
    """Manages Docker containers for code execution."""
    
    def __init__(self, image_name="python-preloaded:3.11"):
        """
        Initialize Docker manager.
        
        Args:
            image_name: Docker image to use (default: python-preloaded:3.11 with common packages)
        """
        self.image_name = image_name
        self.client = None
        
        try:
            # Allow explicit socket override via DOCKER_HOST env var.
            # On Linux with rootless Docker the socket is at
            # unix:///run/user/<UID>/docker.sock rather than /var/run/docker.sock.
            # Set DOCKER_HOST=unix:///run/user/<UID>/docker.sock to point at it.
            docker_host = os.environ.get("DOCKER_HOST")
            if docker_host:
                self.client = docker.DockerClient(base_url=docker_host)
            else:
                self.client = docker.from_env()

            try:
                self.client.images.get(image_name)
                logger.info(f"Docker image {image_name} found")
            except docker.errors.ImageNotFound:
                if _is_custom_local_image(image_name):
                    raise RuntimeError(
                        f"Docker image '{image_name}' was not visible to the active Docker daemon "
                        f"({self.client.api.base_url}). This image is expected to exist locally, so "
                        f"this usually means a Docker context/daemon mismatch rather than a missing registry image."
                    )
                logger.info(f"Pulling Docker image: {image_name}")
                self.client.images.pull(image_name)
                logger.info(f"Successfully pulled {image_name}")
        
        except Exception as e:
            logger.error(f"Docker initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize Docker: {e}")
    
    def create_container(self, host_workdir, container_workdir="/workspace", environment=None):
        """
        Create and start a container with mounted workspace.
        
        Args:
            host_workdir: Path on host machine
            container_workdir: Path in container (default: /workspace)
            environment: Dictionary of environment variables (optional)
        
        Returns:
            Container object
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        host_workdir = os.path.abspath(host_workdir)
        os.makedirs(host_workdir, exist_ok=True)
        
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command="sleep infinity",
                detach=True,
                user="root",
                mem_limit="512m",
                remove=False,
                volumes={
                    host_workdir: {
                        'bind': container_workdir,
                        'mode': 'rw,Z'
                    }
                },
                environment=environment or {}
            )
            
            logger.debug(f"Created container {container.id[:12]} with {host_workdir} mounted at {container_workdir}")
            return container
        
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    def execute_in_container(self, container, command, timeout=30):
        """
        Execute bash command in container.

        Args:
            container: Container object
            command: Bash command to execute (supports operators like &&, |, ;, redirects)
            timeout: Timeout in seconds (enforced via GNU coreutils `timeout`)

        Returns:
            Dictionary with stdout, stderr, exit_code
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")

        # Use bash -c inside `timeout` so complex shell commands are interpreted correctly.
        # Standard `timeout` exits with 124 on timeout (SIGTERM). Do NOT use -s KILL here
        # because that gives exit 137 (SIGKILL), which is indistinguishable from a Docker OOM kill.
        # Exit 137 is reserved for genuine Docker OOM; exit 124 means timed out.
        # --kill-after=5s sends SIGKILL 5s after SIGTERM if the process hasn't exited yet,
        # but the exit code is still 124, preserving the timeout vs OOM distinction.
        wrapped = f"exec timeout --kill-after=5s {int(timeout)}s bash -c {shlex.quote(command)}"

        try:
            exec_result = container.exec_run(
                cmd=["bash", "-lc", wrapped],
                stdout=True,
                stderr=True,
                demux=True,          # get (stdout, stderr) separately
            )

            out, err = exec_result.output
            stdout = (out or b"").decode(errors="replace")
            stderr = (err or b"").decode(errors="replace")
            exit_code = exec_result.exit_code

            if exit_code == 124:
                # Make it obvious to callers that this was a timeout
                msg = f"Command exceeded {timeout}s and was terminated."
                logger.warning(msg)
                stderr = (stderr + ("\n" if stderr else "") + msg).strip()

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            }

        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
            }

    
    def cleanup_container(self, container):
        """
        Stop and remove container.
        
        Args:
            container: Container object
        """
        try:
            container.remove(force=True)
            logger.debug(f"Removed container: {container.id[:12]}")
        except Exception as e:
            logger.warning(f"Failed to cleanup container: {e}")

    def close(self):
        self.client.close()
