from django import forms
from pathlib import Path

class AddAttachmentsForm(forms.Form):
    pdf_base = forms.FileField(label=("PDF Base (.pdf)"))

    def clean_pdf_base(self):
        f = self.cleaned_data["pdf_base"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError("El fitxer base ha de ser un PDF.")  
        return f


class ExtractForm(forms.Form):
    pdf_with_attachments = forms.FileField(label=("PDF amb adjunts"))

    def clean_pdf_with_attachments(self):
        f = self.cleaned_data["pdf_with_attachments"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError("Si us plau pujeu un arxiu PDF.")
        return f