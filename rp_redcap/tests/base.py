from rp_redcap.models import Project
from sidekick.models import Organization


class RedcapBaseTestCase(object):
    def create_project(self, org):
        return Project.objects.create(
            name="Test Project",
            url="http://localhost:8001/",
            token="REPLACEME",
            org=org,
        )

    def create_org(self):
        return Organization.objects.create(
            name="Test Organization",
            url="http://localhost:8002/",
            token="REPLACEME",
        )
