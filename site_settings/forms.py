from django import forms

from .models import SiteSetting


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = (
            "site_name",
            "logo",
            "primary_color",
            "accent_color",
            "footer_text",
            "contact_email",
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_use_tls",
        )
        widgets = {
            "footer_text": forms.Textarea(attrs={"rows": 3}),
            "smtp_password": forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault("class", "file-input")
            else:
                field.widget.attrs.setdefault("class", "input")
