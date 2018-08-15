import cgi

from fixtures import *  # noqa: F401,F403


def mime_type(content_type):
    return cgi.parse_header(content_type)[0]


class TestRPSidekickContainer:
    def test_db_tables_created(
        self, rp_sidekick_container, postgresql_container
    ):
        """
        When the Django container starts, it should run its migrations
        """
        django_logs = rp_sidekick_container.get_logs().decode("utf-8")
        assert "Running migrations" in django_logs

        psql_output = postgresql_container.exec_psql(
            (
                "SELECT COUNT(*) FROM information_schema.tables WHERE "
                "table_schema='public';"
            )
        )
        count = int(psql_output.output.strip())
        assert count > 0

    def test_admin_page(self, rp_sidekick_container, postgresql_container):
        """
        When we try to access the django admin page, it should be returned
        """
        client = rp_sidekick_container.http_client()
        response = client.get("/admin")

        assert response.status_code == 200
        assert mime_type(response.headers["content-type"]) == "text/html"
        assert "<title>Log in | Django site admin</title>" in response.text
