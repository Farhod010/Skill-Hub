from django.db import models


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=120, default="SkillHub")
    logo = models.ImageField(upload_to="site/logo/", blank=True, null=True)
    primary_color = models.CharField(max_length=20, default="#11324d")
    accent_color = models.CharField(max_length=20, default="#d97706")
    footer_text = models.CharField(
        max_length=255,
        default="SkillHub helps ambitious learners turn momentum into mastery.",
    )
    contact_email = models.EmailField(blank=True)
    smtp_host = models.CharField(max_length=120, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=120, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
