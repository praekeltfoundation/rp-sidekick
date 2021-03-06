from django.db import models

from rp_redcap.models import Project
from sidekick import utils


class Hospital(models.Model):
    name = models.CharField(max_length=200, blank=False)
    data_access_group = models.CharField(max_length=200, blank=False)
    project = models.ForeignKey(
        Project, related_name="hospitals", null=False, on_delete=models.CASCADE
    )
    rapidpro_flow = models.CharField(max_length=200)
    hospital_lead_name = models.CharField(max_length=200)
    hospital_lead_urn = models.CharField(max_length=200)
    nomination_name = models.CharField(max_length=200, null=True, blank=True)
    nomination_urn = models.CharField(max_length=200, null=True, blank=True)
    whatsapp_group_id = models.CharField(max_length=200, null=True, blank=True)
    tz_code = models.CharField(max_length=10, default="CAT")
    is_active = models.BooleanField(default=True)

    unique_together = (("name", "project_id"),)

    def __str__(self):
        return "{} - {}".format(self.project.name, self.name)

    def check_and_update_status(self):
        """
        Recruitment stops on the first Monday after the hospital has 100
        cases or after 4 weeks.
        Reminders stop on the Thursday after recruitment stopped.
        We disable the hospital when the reminders should stop.
        """
        screening_record = self.screening_records.first()
        if screening_record and screening_record.date:
            today = utils.get_today()

            total_days = (today - screening_record.date).days
            week_number = total_days // 7

            total_cases = 0
            for i in range(1, week_number + 1):
                week_count = getattr(screening_record, "week_{}_case_count".format(i))
                if week_count:
                    total_cases += week_count

            if total_days >= week_number * 7 + 3 and (
                total_cases >= 100 or week_number >= 4
            ):
                self.is_active = False
                self.save()

    def create_hospital_wa_group(self):
        if not self.whatsapp_group_id:
            # WA group subject is limited to 25 characters
            self.whatsapp_group_id = utils.create_whatsapp_group(
                self.project.org, "{} - ASOS2".format(self.name[:17])
            )
            self.save()

    def get_wa_group_info(self):
        group_info = {"participants": [], "admins": []}
        if self.whatsapp_group_id:
            group_info = utils.get_whatsapp_group_info(
                self.project.org, self.whatsapp_group_id
            )
            group_info["id"] = self.whatsapp_group_id
        return group_info

    def add_group_admins(self, group_info, msisdns):
        wa_ids = []
        for msisdn in msisdns:
            wa_id = utils.get_whatsapp_contact_id(self.project.org, msisdn)
            if wa_id:
                wa_ids.append(wa_id)

        for wa_id in wa_ids:
            if (
                wa_id in group_info["participants"]
                and wa_id not in group_info["admins"]
            ):
                utils.add_whatsapp_group_admin(
                    self.project.org, group_info["id"], wa_id
                )

        return wa_ids

    def send_message(self, message):
        group_info = self.get_wa_group_info()
        rapidpro_client = self.project.org.get_rapidpro_client()

        urns = {self.hospital_lead_urn: self.hospital_lead_name}
        if self.nomination_urn:
            urns[self.nomination_urn] = self.nomination_name

        sent_to_group = False
        for urn, name in urns.items():
            if urn.replace("+", "") in group_info["participants"]:
                if not sent_to_group:
                    sent_to_group = True

                    utils.send_whatsapp_group_message(
                        self.project.org, group_info["id"], message
                    )
            else:
                urns = ["tel:{}".format(urn)]
                utils.update_rapidpro_whatsapp_urn(self.project.org, urn)

                extra_info = {
                    "hospital_name": self.name,
                    "week": utils.get_current_week_number(),
                    "reminder": message,
                    "contact_name": name,
                }

                rapidpro_client.create_flow_start(
                    self.rapidpro_flow,
                    urns,
                    restart_participants=True,
                    extra=extra_info,
                )


class ScreeningRecord(models.Model):
    record_id = models.CharField(max_length=30, null=False, blank=False)
    hospital = models.ForeignKey(
        Hospital, related_name="screening_records", null=False, on_delete=models.CASCADE
    )
    date = models.DateField(null=True)
    week_1_case_count = models.IntegerField(null=True, blank=True)
    week_2_case_count = models.IntegerField(null=True, blank=True)
    week_3_case_count = models.IntegerField(null=True, blank=True)
    week_4_case_count = models.IntegerField(null=True, blank=True)
    total_eligible = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def as_dict(self):
        return {
            "date": self.date.strftime("%Y-%m-%d") if self.date else "",
            "week_1_case_count": self.week_1_case_count,
            "week_2_case_count": self.week_2_case_count,
            "week_3_case_count": self.week_3_case_count,
            "week_4_case_count": self.week_4_case_count,
            "total_eligible": self.total_eligible,
        }


class PatientRecord(models.Model):

    INCOMPLETE_STATUS = "0"
    UNVERIFIED_STATUS = "1"
    COMPLETE_STATUS = "2"

    STATUS_CHOICES = (
        (INCOMPLETE_STATUS, "Incomplete"),
        (UNVERIFIED_STATUS, "Unverified"),
        (COMPLETE_STATUS, "Complete"),
    )
    project = models.ForeignKey(
        Project, related_name="patients", null=False, on_delete=models.CASCADE
    )
    hospital = models.ForeignKey(
        Hospital, related_name="patients", null=True, on_delete=models.CASCADE
    )
    record_id = models.CharField(max_length=30, null=False, blank=False)
    date = models.DateField(null=True)
    pre_operation_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default=INCOMPLETE_STATUS,
    )
    post_operation_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default=INCOMPLETE_STATUS,
    )

    unique_together = (("project", "record_id"),)


class PatientValue(models.Model):
    patient = models.ForeignKey(
        PatientRecord, related_name="values", null=False, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, blank=False)
    value = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    unique_together = (("patient", "name"),)
