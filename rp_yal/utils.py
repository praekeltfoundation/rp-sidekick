import contextlib
from datetime import datetime
from urllib.parse import urljoin

import redis
import requests
from django.conf import settings

redis_conn = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_ordered_content_set(org, fields):
    search_term = None
    fields = clean_contact_fields(fields)

    weekday = datetime.today().weekday()

    if fields.get("test_day"):
        with contextlib.suppress(ValueError):
            weekday = int(fields.get("test_day")) - 1

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


def get_content_search_term(fields, last_topic_sent=None):
    if not last_topic_sent:
        last_topic_sent = fields.get("last_topic_sent", "")

    risks = {
        "depression": "depression_and_anxiety_risk",
        "gender attitudes": "gender_attitude_risk",
        "self perceived healthcare": "selfperceived_healthcare_risk",
        "body image": "body_image_risk",
        "connectedness": "connectedness_risk",
    }

    def all_complete():
        return (
            fields.get("depression_content_complete", "") == "true"
            and fields.get("gender_attitude_content_complete", "") == "true"
            and fields.get("selfperceived_healthcare_complete", "") == "true"
            and fields.get("body_image_content_complete", "") == "true"
            and fields.get("connectedness_content_complete", "") == "true"
        )

    if fields.get("depression_and_anxiety_risk", "") == "low_risk":
        if last_topic_sent == "depression":
            if fields.get("gender_attitude_content_complete", "") == "true":
                return get_content_search_term(fields, "gender attitudes")
            else:
                next_topic = "gender attitudes"
        elif last_topic_sent == "gender attitudes":
            if fields.get("selfperceived_healthcare_complete", "") == "true":
                return get_content_search_term(fields, "self perceived healthcare")
            else:
                return "self perceived healthcare"
        elif last_topic_sent == "self perceived healthcare":
            if fields.get("body_image_content_complete", "") == "true":
                return get_content_search_term(fields, "body image")
            else:
                next_topic = "body image"
        elif last_topic_sent == "body image":
            if fields.get("connectedness_content_complete", "") == "true":
                return get_content_search_term(fields, "connectedness")
            else:
                next_topic = "connectedness"
        else:
            if fields.get("depression_content_complete", "") == "true":
                if all_complete():
                    return None
                else:
                    return get_content_search_term(fields, "depression")
            else:
                next_topic = "depression"
    else:
        if last_topic_sent == "self perceived healthcare":
            if fields.get("gender_attitude_content_complete", "") == "true":
                return get_content_search_term(fields, "gender attitudes")
            else:
                next_topic = "gender attitudes"
        elif last_topic_sent == "body image":
            if fields.get("selfperceived_healthcare_complete", "") == "true":
                return get_content_search_term(fields, "self perceived healthcare")
            else:
                return "self perceived healthcare"
        elif last_topic_sent == "connectedness":
            if fields.get("body_image_content_complete", "") == "true":
                return get_content_search_term(fields, "body image")
            else:
                next_topic = "body image"
        elif last_topic_sent == "depression":
            if fields.get("connectedness_content_complete", "") == "true":
                return get_content_search_term(fields, "connectedness")
            else:
                next_topic = "connectedness"
        else:
            if fields.get("depression_content_complete", "") == "true":
                if all_complete():
                    return None
                else:
                    return get_content_search_term(fields, "depression")
            else:
                next_topic = "depression"

    risk_label = "high-risk"
    if "low" in fields.get(risks[next_topic], ""):
        risk_label = "mandatory"
    return f"{next_topic} {risk_label}"


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
    key_name = f"page_seen_ids_{msisdn}"

    if redis_conn.get(key_name):
        return [int(id) for id in redis_conn.get(key_name).split(",")]

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
    ids = [p["page"] for p in pages_seen["results"]]

    value = ",".join([str(id) for id in ids])
    redis_conn.set(key_name, value)
    redis_conn.expire(key_name, time=5 * 60 * 60)

    return ids


def get_contentrepo_headers(org):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {org.contentrepo_token}",
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
    contentset_data["pages_seen_ids"] = pages_seen_ids

    return contentset_data
