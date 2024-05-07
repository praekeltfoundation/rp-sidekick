from unittest.mock import patch

import responses
from django.test import TestCase
from freezegun import freeze_time

from rp_yal import utils
from sidekick.tests.utils import create_org

TEST_CONTENT_SETS = [
    {
        "id": 1,
        "name": "Connectedness Mandatory Female relationship",
        "field_count": 2,
        "gender": "female",
        "relationship": "in_a_relationship",
    },
    {
        "id": 2,
        "name": "Connectedness Mandatory relationship",
        "field_count": 1,
        "relationship": "in_a_relationship",
    },
    {
        "id": 3,
        "name": "Connectedness Mandatory ",
        "field_count": 0,
    },
]


class TestGetOrderedContentSet(TestCase):
    def setUp(self):
        self.org = create_org()

    @freeze_time("2024-05-05 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    def test_get_ordered_content_set_weekend(self, mock_search_ocs):
        """
        On the weekend it shouldn't attempt anything
        """
        contentset_id = utils.get_ordered_content_set(self.org, {})

        self.assertIsNone(contentset_id)
        mock_search_ocs.assert_not_called()

    @freeze_time("2024-05-06 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    def test_get_ordered_content_set_monday(self, mock_first_mcs, mock_search_ocs):
        """
        On a Monday if a contact has no fields set the it will search for low lit sets
        and return the first one that matches profile.
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1

        fields = {
            "gender": "male",
            "relationship_status": "yes",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "low lit")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)

    @freeze_time("2024-05-06 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    @patch("rp_yal.utils.get_content_search_term")
    def test_get_ordered_content_set_monday_ed_completed(
        self, mock_get_search_term, mock_first_mcs, mock_search_ocs
    ):
        """
        On a Monday, if a contact has finished the education content, it will search
        for the depression content set and return the first one that matches profile
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1
        mock_get_search_term.return_value = "depression"

        fields = {
            "gender": "male",
            "relationship_status": "yes",
            "educational_content_completed": "true",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "depression")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)
        mock_get_search_term.assert_called_with(fields)

    @freeze_time("2024-05-06 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    @patch("rp_yal.utils.get_content_search_term")
    def test_get_ordered_content_set_monday_sex_lit_low(
        self, mock_get_search_term, mock_first_mcs, mock_search_ocs
    ):
        """
        On a Monday, if the contact finished education content and sexual health
        literacy is low, it will search for fun content sets and return the first one
        that matches the profile
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1

        fields = {
            "gender": "male",
            "relationship_status": "yes",
            "educational_content_completed": "true",
            "sexual_health_lit_risk": "low",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "fun")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)
        mock_get_search_term.assert_not_called()

    @freeze_time("2024-05-06 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    @patch("rp_yal.utils.get_content_search_term")
    def test_get_ordered_content_set_monday_sex_lit_low_fun_completed(
        self, mock_get_search_term, mock_first_mcs, mock_search_ocs
    ):
        """
        On a Monday, if the contact finished education content and sexual health
        literacy is low and fun content is completed, it will search for depression
        content sets and return the first one that matches the profile
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1
        mock_get_search_term.return_value = "depression"

        fields = {
            "gender": "male",
            "relationship_status": "yes",
            "educational_content_completed": "true",
            "sexual_health_lit_risk": "low",
            "fun_content_completed": "true",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "depression")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)
        mock_get_search_term.assert_called_with(fields)

    @freeze_time("2024-05-07 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    def test_get_ordered_content_set_tuesday(self, mock_first_mcs, mock_search_ocs):
        """
        On a tuesday to friday if a contact with no other fields set and hasn't
        completed the push message intro set, it will return the high risk intro
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1

        fields = {
            "gender": "male",
            "relationship_status": "yes",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "intro high-risk")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)

    @freeze_time("2024-05-07 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    def test_get_ordered_content_set_tuesday_low_risk(
        self, mock_first_mcs, mock_search_ocs
    ):
        """
        On a tuesday to friday if a contact depression_and_anxiety_risk is low and
        hasn't completed the push message intro set, it will return the low risk intro
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1

        fields = {
            "gender": "male",
            "relationship_status": "yes",
            "depression_and_anxiety_risk": "low_risk",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "intro low-risk")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)

    @freeze_time("2024-05-07 01:30:00")
    @patch("rp_yal.utils.search_ordered_content_sets")
    @patch("rp_yal.utils.get_first_matching_content_set")
    @patch("rp_yal.utils.get_content_search_term")
    def test_get_ordered_content_set_tuesday_intro_completed(
        self, mock_get_search_term, mock_first_mcs, mock_search_ocs
    ):
        """
        On a tuesday to friday if a contact has completed the push messages intro, it
        will search for depression content sets and return the first one that matches
        the profile
        """
        mock_search_ocs.return_value = TEST_CONTENT_SETS
        mock_first_mcs.return_value = 1
        mock_get_search_term.return_value = "depression"

        fields = {
            "gender": "male",
            "relationship_status": "yes",
            "push_msg_intro_completed": "true",
        }
        contentset_id = utils.get_ordered_content_set(self.org, fields)

        self.assertEqual(contentset_id, 1)
        mock_search_ocs.assert_called_with(self.org, "depression")
        mock_first_mcs.assert_called_with(TEST_CONTENT_SETS, fields)


class TestCleanContactFields(TestCase):

    def test_clean_contact_fields(self):
        fields = {
            "test 1": None,
            "test 2": "Test",
            "test 3": 1,
        }
        clean_fields = utils.clean_contact_fields(fields)

        self.assertEqual(clean_fields, {"test 2": "test", "test 3": 1})


class GetRelationshipStatusTestCase(TestCase):
    def test_get_relationship_status_empty(self):
        status = utils.get_relationship_status("")
        self.assertEqual(status, "single")

    def test_get_relationship_status_relationship(self):
        status = utils.get_relationship_status("relationship")
        self.assertEqual(status, "in_a_relationship")

    def test_get_relationship_status_yes(self):
        status = utils.get_relationship_status("yes")
        self.assertEqual(status, "in_a_relationship")

    def test_get_relationship_status_single(self):
        status = utils.get_relationship_status("single")
        self.assertEqual(status, "single")

    def test_get_relationship_status_no(self):
        status = utils.get_relationship_status("no")
        self.assertEqual(status, "single")

    def test_get_relationship_status_complicated(self):
        status = utils.get_relationship_status("complicated")
        self.assertEqual(status, "single")


class GetGenderTestCase(TestCase):
    def test_get_gender_empty(self):
        status = utils.get_gender("")
        self.assertEqual(status, "empty")

    def test_get_gender(self):
        status = utils.get_gender("Non_Binary")
        self.assertEqual(status, "non-binary")


class GetContentSearchTerm(TestCase):
    def test_get_content_search_term_low_risk(self):
        """
        If the depression and anxiety risk is low then return first item in list with
        mandatory
        """
        fields = {"depression_and_anxiety_risk": "low_risk"}
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "depression mandatory")

    def test_get_content_search_term_high_risk(self):
        """
        If the depression and anxiety risk is high then return first item in list with
        high-risk
        """
        fields = {"depression_and_anxiety_risk": "high_risk"}
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "depression high-risk")

    def test_get_content_search_term_high_risk_depression_completed(self):
        """
        If depression content is complete return the next one in the high risk flow,
        connectedness
        """
        fields = {
            "depression_and_anxiety_risk": "high_risk",
            "depression_content_complete": "true",
        }
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "connectedness high-risk")

    def test_get_content_search_term_high_risk_half_completed(self):
        """
        Loop through flow until we find one that isn't completed
        """
        fields = {
            "depression_and_anxiety_risk": "high_risk",
            "depression_content_complete": "true",
            "connectedness_content_complete": "true",
        }
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "body image high-risk")

    def test_get_content_search_term_high_risk_all_completed(self):
        """
        If all contentsets are completed return empty string
        """
        fields = {
            "depression_and_anxiety_risk": "high_risk",
            "depression_content_complete": "true",
            "connectedness_content_complete": "true",
            "body_image_content_complete": "true",
            "selfperceived_healthcare_complete": "true",
            "gender_attitude_content_complete": "true",
        }
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "")

    def test_get_content_search_term_high_risk_with_last_topic(self):
        """
        If last topic is set we start looping from there
        """
        fields = {"last_topic_sent": "connectedness"}
        search_term = utils.get_content_search_term(fields)
        self.assertEqual(search_term, "body image high-risk")


class SearchOrderedContentSetsTestcase(TestCase):
    def setUp(self):
        self.org = create_org()

    @responses.activate
    def test_search_ordered_content_sets(self):
        responses.add(
            method=responses.GET,
            url="http://contentrepo/api/v2/orderedcontent/",
            json={
                "count": 2,
                "next": True,
                "previous": None,
                "results": [
                    {
                        "id": 154,
                        "name": "Connectedness Mandatory Female Single",
                        "profile_fields": [
                            {"profile_field": "gender", "value": "female"},
                            {"profile_field": "relationship", "value": "single"},
                        ],
                    },
                    {
                        "id": 159,
                        "name": "Connectedness Mandatory Male Single",
                        "profile_fields": [
                            {"profile_field": "gender", "value": "male"},
                            {"profile_field": "relationship", "value": "single"},
                        ],
                    },
                ],
            },
            status=200,
            match=[
                responses.matchers.query_param_matcher(
                    {"search": "Connectedness Mandatory"}
                )
            ],
        )

        responses.add(
            method=responses.GET,
            url="http://contentrepo/api/v2/orderedcontent/",
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 164,
                        "name": "Connectedness Mandatory Female Single",
                        "profile_fields": [
                            {"profile_field": "gender", "value": "female"},
                            {"profile_field": "relationship", "value": "single"},
                        ],
                    },
                    {
                        "id": 169,
                        "name": "Connectedness Mandatory Male Single",
                        "profile_fields": [
                            {"profile_field": "gender", "value": "male"},
                            {"profile_field": "relationship", "value": "single"},
                        ],
                    },
                ],
            },
            status=200,
            match=[
                responses.matchers.query_param_matcher(
                    {"search": "Connectedness Mandatory", "page": 2}
                )
            ],
        )

        contentsets = utils.search_ordered_content_sets(
            self.org, "Connectedness Mandatory"
        )

        self.assertEqual(len(contentsets), 4)
        self.assertEqual(contentsets[0]["field_count"], 2)
        self.assertEqual(contentsets[0]["gender"], "female")
        self.assertEqual(contentsets[0]["relationship"], "single")


class GetFirstMatchingContentSet(TestCase):
    def test_get_first_matching_content_set_two_matches(self):
        fields = {"gender": "female", "relationship_status": "relationship"}
        contentset_id = utils.get_first_matching_content_set(TEST_CONTENT_SETS, fields)

        self.assertEqual(contentset_id, 1)

    def test_get_first_matching_content_set_one_match(self):
        fields = {"relationship_status": "relationship"}
        contentset_id = utils.get_first_matching_content_set(TEST_CONTENT_SETS, fields)

        self.assertEqual(contentset_id, 2)

    def test_get_first_matching_content_set_no_matches(self):
        fields = {"relationship_status": "single"}
        contentset_id = utils.get_first_matching_content_set(TEST_CONTENT_SETS, fields)

        self.assertEqual(contentset_id, 3)
