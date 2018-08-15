import pytest
from seaworthy.definitions import ContainerDefinition
from seaworthy.containers.postgresql import PostgreSQLContainer

RP_SIDEKICK_IMAGE = pytest.config.getoption("--rp-sidekick-image")


class RPSidekickContainer(ContainerDefinition):
    WAIT_PATTERNS = (r"Listening at: unix:/var/run/gunicorn/gunicorn.sock",)

    def __init__(self, name, db_url, image=RP_SIDEKICK_IMAGE):
        super().__init__(name, image, self.WAIT_PATTERNS)
        self.db_url = db_url

    def base_kwargs(self):
        return {
            "ports": {"8000/tcp": None},
            "environment": {"RP_SIDEKICK_IMAGE": self.db_url},
        }


postgresql_container = PostgreSQLContainer("postgresql")
postgresql_fixture, clean_postgresql_fixture = postgresql_container.pytest_clean_fixtures(
    "postgresql_container"
)

rp_sidekick_container = RPSidekickContainer(
    "ndoh-hub", postgresql_container.database_url()
)
rp_sidekick_fixture = rp_sidekick_container.pytest_fixture(
    "rp_sidekick_container", dependencies=["postgresql_container"]
)

__all__ = [
    "clean_postgresql_fixture",
    "rp_sidekick_fixture",
    "postgresql_fixture",
]
