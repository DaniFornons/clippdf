from django import forms
from pathlib import Path
from django.utils.translation import gettext_lazy as _ 

class AddAttachmentsForm(forms.Form):
    pdf_base = forms.FileField(label=_("Base PDF (.pdf)"))  

    def clean_pdf_base(self):
        f = self.cleaned_data["pdf_base"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError(_("The base file must be a PDF."))  
        return f


class ExtractForm(forms.Form):
    pdf_with_attachments = forms.FileField(label=_("PDF with embedded attachments (.pdf)"))  

    def clean_pdf_with_attachments(self):
        f = self.cleaned_data["pdf_with_attachments"]
        if Path(f.name).suffix.lower() != ".pdf":
            raise forms.ValidationError(_("Please upload a .pdf file."))  
        return f
