from json2html import json2html

from urllib.parse import urlparse, parse_qs, urljoin

import pandas as pd

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.generic import View

from .forms import CheckFlowsForm


"""
    "29c9575c-e605-4938-bed3-361833e576dd"
    "1daa0b98-29c0-4c12-8a84-3517fb846166"
    "f0a888d9-4e33-4028-80af-5db42194a724" # EXAM-FP-pretrial-attributes-randomization
    "f0696eba-ed03-409e-ae15-227b3bcc75e0" # EXAM-FP-pretrial-attributes-thankyou
    "ff2b9364-9118-4a72-b4a6-78629607b01b" # EXAM-FP-pretrial-attributes-invitation
    "f77728cd-e66b-40b3-8978-672d77cecec3" # EXAM-FP-pretrial-attributes-questionspassive
    "42372ec1-f8e4-47ab-8807-e10c2fae75ff" #
    "21c49bdb-7565-4998-afd5-53f2719b3180" # auto-response
"""


def flatten(_list):
    return [item for sublist in _list for item in sublist]


def color_boolean(val):
    if type(val) == bool:
        color = "green" if val else "red"
    else:
        color = "black"
    return "color: {}".format(color)


def get_actions(flow_defintion):
    """
    Returns a flat list of all actions within a flow
    """
    return flatten(
        [action_set["actions"] for action_set in flow_defintion["action_sets"]]
    )


# Create your views here.
class CheckVariables(LoginRequiredMixin, View):
    # form_class = CheckFlowsForm

    def get(self, request, *args, **kwargs):
        template = loader.get_template("rp_checker/check_variables.html")
        return HttpResponse(
            template.render({"form": CheckFlowsForm()}, request)
        )

    def post(self, request, *args, **kwargs):
        template = loader.get_template("rp_checker/check_variables.html")
        form = CheckFlowsForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data["org"].get_rapidpro_client()
            flow_uuids = form.cleaned_data["uuids"]

            flow_definitions = []
            for flow_uuid in flow_uuids:
                for definition in client.get_definitions(
                    flows=(flow_uuid), dependencies=None
                ).flows:
                    if definition["metadata"]["uuid"] == flow_uuid:
                        flow_definitions.append(definition)
                        break

            if len(flow_definitions) != len(flow_uuids):
                return HttpResponse("Something went wrong fetching the flows")

            # Get all of the replies and check that they match
            all_labels = []
            flow_labels = []
            for flow_definition in flow_definitions:
                labels = []
                for rule_set in flow_definition["rule_sets"]:
                    labels.append(rule_set["label"])
                    all_labels.append(rule_set["label"])
                flow_labels.append(
                    {
                        "name": flow_definition["metadata"]["name"],
                        "labels": labels,
                    }
                )

            # get labels
            all_labels = list(set(all_labels))

            d = {"Labels": all_labels}
            for flow in flow_labels:
                d[flow["name"]] = [
                    (label in flow["labels"]) for label in all_labels
                ]

            df = pd.DataFrame(d)
            return HttpResponse(
                template.render(
                    {
                        "form": form,
                        "table": (
                            df.sort_values(["Labels"])
                            .style.applymap(color_boolean)
                            .render(index=False)
                        ),
                    },
                    request,
                )
            )
        return HttpResponse(template.render({"form": form}, request))


class CheckWebhooks(LoginRequiredMixin, View):
    """
    FLOW
    SECURE: YES/NO !
    URL: PATH
    NAME/LABEL:
    QUERY PARAMS:
        foo: bar (might be rapidpro variable)
        baz: bob
    HEADERS:
        foo: bar
        baz: bob
    RULE:
        SUCCESS: YES/NO
        FAILURE: YES/NO
    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template("rp_checker/check_webhooks.html")
        return HttpResponse(
            template.render({"form": CheckFlowsForm()}, request)
        )

    def post(self, request, *args, **kwargs):
        form = CheckFlowsForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data["org"].get_rapidpro_client()
            flow_uuids = form.cleaned_data["uuids"]

            flow_definitions = []
            for flow_uuid in flow_uuids:
                for definition in client.get_definitions(
                    flows=(flow_uuid), dependencies=None
                ).flows:
                    if definition["metadata"]["uuid"] == flow_uuid:
                        flow_definitions.append(definition)
                        break

            if len(flow_definitions) != len(flow_uuids):
                return HttpResponse("Something went wrong fetching the flows")

            webhook_audit_results = []
            for the_flow in flow_definitions:
                # go through the definition and find the webhooks
                webhooks = [
                    rule_set
                    for rule_set in the_flow["rule_sets"]
                    if rule_set["ruleset_type"] == "webhook"
                ]

                # check the URL and the headers
                for webhook in webhooks:
                    url = webhook["config"]["webhook"]
                    parsed_url = urlparse(url)
                    query_string = parse_qs(parsed_url.query)

                    webhook_audit_result = {
                        "FlowName": the_flow["metadata"]["name"],
                        "UsesHTTPS": str(parsed_url.scheme == "https"),
                        "RequestType": "GET",
                        "Path": urljoin(parsed_url.hostname, parsed_url.path),
                        "QueryParams": query_string,
                        "Headers": webhook["config"]["webhook_headers"],
                        "Rules": {
                            # "Success": (webhook[0]["destination"] is None) for webhook in rules if webhook["category"]["base"].lower() == "success",
                            # "Failure": (webhook[0]["destination"] is None)  for webhook in rules if webhook["category"]["base"].lower() == "failure",
                            "Success": True,
                            "Failure": False,
                        },
                    }
                    webhook_audit_results.append(webhook_audit_result)

            template = loader.get_template("rp_checker/check_webhooks.html")
            return HttpResponse(
                template.render(
                    {
                        "form": form,
                        "tables": [
                            json2html.convert(_webhook_audit_result)
                            for _webhook_audit_result in webhook_audit_results
                        ],
                    },
                    request,
                )
            )


class CheckFlowLinks(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        template = loader.get_template("rp_checker/check_webhooks.html")
        return HttpResponse(
            template.render({"form": CheckFlowsForm()}, request)
        )

    def post(self, request, *args, **kwargs):
        """
        "action_sets": [
                {
                    "uuid": "edfe94e0-034d-4aec-91ab-e594a911edd4",
                    "x": 606,
                    "y": 204,
                    "destination": null,
                    "actions": [
                        {
                            "type": "flow",
                            "uuid": "3d6e265e-1844-45c6-ad34-3ac893aea0bc",
                            "flow": {
                                "uuid": "ff2b9364-9118-4a72-b4a6-78629607b01b",
                                "name": "EXAM-FP-pretrial-attributes-invitation"
                            }
                        }
                    ],
                    "exit_uuid": "48415678-045d-4b42-a21c-523d8edcde25"
                }
            ],
        """
        form = CheckFlowsForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data["org"].get_rapidpro_client()
            flow_uuids = [
                "ff2b9364-9118-4a72-b4a6-78629607b01b",
                "1daa0b98-29c0-4c12-8a84-3517fb846166",
                "29c9575c-e605-4938-bed3-361833e576dd",
                "f0a888d9-4e33-4028-80af-5db42194a724",
                "f0696eba-ed03-409e-ae15-227b3bcc75e0",
                "f77728cd-e66b-40b3-8978-672d77cecec3",
                "42372ec1-f8e4-47ab-8807-e10c2fae75ff",
                "21c49bdb-7565-4998-afd5-53f2719b3180",
            ]

            flow_definitions = []
            for flow_uuid in flow_uuids:
                for definition in client.get_definitions(
                    flows=(flow_uuid), dependencies=None
                ).flows:
                    if definition["metadata"]["uuid"] == flow_uuid:
                        flow_definitions.append(definition)
                        break

            if len(flow_definitions) != len(flow_uuids):
                return HttpResponse("Something went wrong fetching the flows")

            name_data = {}
            info = {}
            # for each flow, get the name and the uuid
            for flow_definition in flow_definitions:
                uuid = flow_definition["metadata"]["uuid"]
                name_data[uuid] = flow_definition["metadata"]["name"]

                info[flow_definition["metadata"]["uuid"]] = [
                    action["flow"]["uuid"]
                    for action in get_actions(flow_definition)
                    if action["type"] == "flow"
                ]

            return JsonResponse({"data": info})
            # get all of the action sets
            #   get all of the actions
            # iterate through each action, making a list of UUIDS of each of the flows

            # iterate through each flow, checking if that flow starts any of the column flows
