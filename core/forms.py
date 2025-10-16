from django import forms
from pathlib import Path

class AddAttachmentsForm(forms.Form):
    pdf_base = forms.FileField(label="Base PDF (.pdf)")

    def clean_pdf_base(self):
        f = self.cleaned_data["pdf_base"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError("The base file must be a PDF.")
        return f

class ExtractForm(forms.Form):
    pdf_with_attachments = forms.FileField(label="PDF with embedded attachments (.pdf)")

    def clean_pdf_with_attachments(self):
        f = self.cleaned_data["pdf_with_attachments"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError("Please upload a .pdf file.")
        return f