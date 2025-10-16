from io import BytesIO
import unicodedata
from django.shortcuts import render
from django.http import FileResponse, HttpResponseBadRequest
from pypdf import PdfReader, PdfWriter
from .forms import AddAttachmentsForm

def safe_name(name: str) -> str:
    # Normalize accents/whitespace to avoid issues inside the PDF’s attachment names
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return (name or "attachment").replace(" ", "_")

def home(request):
    return render(request, "core/add.html", {"form": AddAttachmentsForm()})

def generate(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")

    form = AddAttachmentsForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "core/add.html", {"form": form}, status=400)

    pdf_base = form.cleaned_data["pdf_base"]
    attachments = request.FILES.getlist("attachments")  # multiple input
    if not attachments:
        return render(request, "core/add.html", {"form": form, "error": "Please select at least one file to attach."}, status=400)

    try:
        pdf_base.seek(0)
        reader = PdfReader(pdf_base)
        writer = PdfWriter()

        # copy pages
        for page in reader.pages:
            writer.add_page(page)

        # unique filenames to avoid collisions
        used = set()
        def unique(n):
            base, dot, ext = n.rpartition(".")
            cand, i = n, 1
            while cand in used:
                cand = f"{base}_{i}.{ext}" if ext else f"{n}_{i}"
                i += 1
            used.add(cand)
            return cand

        # add each file as embedded attachment
        for f in attachments:
            f.seek(0)
            name = unique(safe_name(f.name))
            writer.add_attachment(name, f.read())

        buf = BytesIO()
        writer.write(buf)
        writer.close()
        buf.seek(0)

        stem = pdf_base.name.rsplit(".", 1)[0]
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f"{safe_name(stem)}_with_attachments.pdf",
            content_type="application/pdf",
        )
    except Exception as e:
        return render(request, "core/add.html", {"form": form, "error": f"An error occurred: {e}"}, status=500)
