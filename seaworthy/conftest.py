import os


def pytest_addoption(parser):
    parser.addoption(
        "--rp-sidekick-image",
        action="store",
        default=os.environ.get(
            "RP_SIDEKICK_IMAGE", "praekeltfoundation/rp-sidekick:develop"
        ),
        help="RP Sidekick image to test",
    )


def pytest_report_header(config):
    return "RP Sidekick Docker image: {}".format(
        config.getoption("--rp-sidekick-image")
    )
