from django import forms


class PanelSearchForm(forms.Form):
    q = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update(
            {"class": "input", "placeholder": "Search..."}
        )
