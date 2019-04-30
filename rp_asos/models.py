from django.db import models

from sidekick import utils

from rp_redcap.models import Project


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

    def send_group_invites(self, group_info, wa_ids):
        invites = []
        for wa_id in wa_ids:
            if wa_id not in group_info["participants"]:
                invites.append(wa_id)

        if invites:
            invite_link = utils.get_whatsapp_group_invite_link(
                self.project.org, group_info["id"]
            )
            for wa_id in invites:
                utils.send_whatsapp_template_message(
                    self.project.org,
                    wa_id,
                    "whatsapp:hsm:npo:praekeltpbc",
                    "asos2_notification2",
                    {
                        "default": "Hi, please join the ASOS2 Whatsapp group: {}".format(
                            invite_link
                        )
                    },
                )

    def add_group_admins(self, group_info, wa_ids):
        for wa_id in wa_ids:
            if (
                wa_id in group_info["participants"]
                and wa_id not in group_info["admins"]
            ):
                utils.add_whatsapp_group_admin(
                    self.project.org, group_info["id"], wa_id
                )

    def send_message(self, reminders):
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
                        self.project.org, group_info["id"], "\n".join(reminders)
                    )
            else:
                urns = ["tel:{}".format(urn)]
                utils.update_rapidpro_whatsapp_urn(self.project.org, urn)

                extra_info = {
                    "hospital_name": self.name,
                    "week": utils.get_current_week_number(),
                    "reminder": "\n".join(reminders),
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
        Hospital,
        related_name="screening_records",
        null=False,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    week_day_1 = models.IntegerField(null=True, blank=True)
    week_day_2 = models.IntegerField(null=True, blank=True)
    week_day_3 = models.IntegerField(null=True, blank=True)
    week_day_4 = models.IntegerField(null=True, blank=True)
    week_day_5 = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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
    record_id = models.CharField(max_length=30, null=False, blank=False)
    date = models.DateField()
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
        PatientRecord,
        related_name="values",
        null=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200, blank=False)
    value = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    unique_together = (("patient", "name"),)
