from datetime import datetime
from urllib.parse import urljoin

import requests


def get_ordered_content_set(org, fields):
    search_term = None
    fields = clean_contact_fields(fields)

    weekday = datetime.today().weekday()

    if weekday == 0:
        # Monday
        if "low" in fields.get("sexual_health_lit_risk", ""):
            if fields.get("fun_content_completed", "") == "true":
                search_term = get_content_search_term(fields)
            else:
                search_term = "fun"
        else:
            if fields.get("educational_content_completed", "") == "true":
                search_term = get_content_search_term(fields)
            else:
                search_term = "low lit"
    elif weekday <= 4:
        # Tuesday to Friday
        if fields.get("push_msg_intro_completed", "") == "true":
            search_term = get_content_search_term(fields)
        else:
            if fields.get("depression_and_anxiety_risk", "") == "low_risk":
                search_term = "intro low-risk"
            else:
                search_term = "intro high-risk"

    if search_term:
        contentsets = search_ordered_content_sets(org, search_term)
        return get_first_matching_content_set(contentsets, fields)

    return None


def clean_contact_fields(fields):
    new_fields = {}
    for key, value in fields.items():
        if value:
            try:
                new_fields[key] = int(value)
            except ValueError:
                new_fields[key] = value.lower()
    return new_fields


def get_relationship_status(rp_rel_status):
    if rp_rel_status and rp_rel_status in ("relationship", "yes"):
        return "in_a_relationship"

    return "single"


def get_gender(rp_gender):
    if not rp_gender:
        return "empty"

    return rp_gender.replace("_", "-").lower()


def get_content_search_term(fields):
    last_topic_sent = fields.get("last_topic_sent", "")

    if fields.get("depression_and_anxiety_risk", "") == "low_risk":
        flow = {
            "depression": {
                "complete": "depression_content_complete",
                "next": "gender attitudes",
                "risk": "depression_and_anxiety_risk",
            },
            "gender attitudes": {
                "complete": "gender_attitude_content_complete",
                "next": "self perceived healthcare",
                "risk": "gender_attitude_risk",
            },
            "self perceived healthcare": {
                "complete": "selfperceived_healthcare_complete",
                "next": "body image",
                "risk": "selfperceived_healthcare_risk",
            },
            "body image": {
                "complete": "body_image_content_complete",
                "next": "connectedness",
                "risk": "body_image_risk",
            },
            "connectedness": {
                "complete": "connectedness_content_complete",
                "next": "",
                "risk": "connectedness_risk",
            },
        }
    else:
        flow = {
            "depression": {
                "complete": "depression_content_complete",
                "next": "connectedness",
                "risk": "depression_and_anxiety_risk",
            },
            "connectedness": {
                "complete": "connectedness_content_complete",
                "next": "body image",
                "risk": "connectedness_risk",
            },
            "body image": {
                "complete": "body_image_content_complete",
                "next": "self perceived healthcare",
                "risk": "body_image_risk",
            },
            "self perceived healthcare": {
                "complete": "selfperceived_healthcare_complete",
                "next": "gender attitudes",
                "risk": "selfperceived_healthcare_risk",
            },
            "gender attitudes": {
                "complete": "gender_attitude_content_complete",
                "next": "",
                "risk": "gender_attitude_risk",
            },
        }

    def get_next_topic_and_risk(last):
        if not last:
            next = "depression"
        else:
            next = flow[last]["next"]

        if not next:
            return ""

        if fields.get(flow[next]["complete"], "") == "true":
            return get_next_topic_and_risk(next)
        else:
            risk_label = "high-risk"
            if "low" in fields.get(flow[next]["risk"], ""):
                risk_label = "mandatory"
            return f"{next} {risk_label}"

    return get_next_topic_and_risk(last_topic_sent)


def search_ordered_content_sets(org, search_term):
    page = 1
    next = True

    params = {"search": search_term}

    contentsets = []
    while next:
        if page > 1:
            params["page"] = page

        response = requests.get(
            urljoin(org.contentrepo_url, "api/v2/orderedcontent/"),
            headers=get_contentrepo_headers(org),
            params=params,
        )
        response.raise_for_status()

        response_data = response.json()

        for contentset in response_data["results"]:
            contentset["field_count"] = len(contentset["profile_fields"])
            for field in contentset["profile_fields"]:
                contentset[field["profile_field"]] = field["value"]
            contentsets.append(contentset)

        next = response_data["next"]
        page += 1

    return contentsets


def get_first_matching_content_set(contentsets, fields):
    relationship_status = get_relationship_status(fields.get("relationship_status", ""))
    gender = get_gender(fields.get("gender", ""))

    for contentset in sorted(contentsets, key=lambda d: d["field_count"], reverse=True):
        if contentset["field_count"] == 2:
            if (
                contentset["gender"] == gender
                and contentset["relationship"] == relationship_status
            ):
                return contentset["id"]
        if contentset["field_count"] == 1:

            if contentset["relationship"] == relationship_status:
                return contentset["id"]
        if contentset["field_count"] == 0:
            return contentset["id"]


def get_unique_page_seen_ids(org, msisdn):
    params = {
        "data__user_addr": msisdn,
        "unique_pages": "true",
    }
    response = requests.get(
        urljoin(org.contentrepo_url, "api/v2/custom/pageviews/"),
        headers=get_contentrepo_headers(org),
        params=params,
    )
    response.raise_for_status()

    pages_seen = response.json()
    return [p["page"] for p in pages_seen["results"]]


def get_contentrepo_headers(org):
    return {
        "Content-Type": "application/json",
        "Authorization": "Token {}".format(org.contentrepo_token),
    }


def get_contentset(org, contentset_id, msisdn):
    pages_seen_ids = get_unique_page_seen_ids(org, msisdn)

    params = {
        "show_related": "true",
        "show_tags": "true",
    }
    response = requests.get(
        urljoin(org.contentrepo_url, f"api/v2/orderedcontent/{contentset_id}"),
        headers=get_contentrepo_headers(org),
        params=params,
    )
    response.raise_for_status()
    contentset_data = response.json()

    unseen_pages = []
    for page in contentset_data["pages"]:
        if page["id"] not in pages_seen_ids:
            unseen_pages.append(page)
    contentset_data["pages"] = unseen_pages

    return contentset_data
