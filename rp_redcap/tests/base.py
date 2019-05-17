from rp_redcap.models import Project
from sidekick.models import Organization


class RedcapBaseTestCase(object):
    def create_project(self, org):
        return Project.objects.create(
            name="Test Project",
            url="http://localhost:8001/",
            token="REPLACEME",
            crf_token="REPLACEME_CRF",
            org=org,
            pre_operation_fields="pre_op_field_1,pre_op_field_2",
            post_operation_fields="post_op_field_1,post_op_field_2",
        )

    def create_org(self):
        return Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
        )
