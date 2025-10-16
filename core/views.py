from io import BytesIO
import unicodedata
from django.shortcuts import render
from django.http import FileResponse, HttpResponseBadRequest
from pypdf import PdfReader, PdfWriter
from .forms import AddAttachmentsForm, ExtractForm
from zipfile import ZipFile

def safe_name(name: str) -> str:
    # Normalize accents/whitespace to avoid issues inside the PDF’s attachment names
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return (name or "attachment").replace(" ", "_")

def home(request):
    return render(request, "core/add.html", {"form": AddAttachmentsForm()})

def generate(request):
    if request.method == "GET":
        return render(request, "core/add.html", {"form": AddAttachmentsForm()})
    
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

def extract(request):
    if request.method == "GET":
        return render(request, "core/extract.html", {"form": ExtractForm()})

    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")

    form = ExtractForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "core/extract.html", {"form": form}, status=400)

    pdf = form.cleaned_data["pdf_with_attachments"]

    try:
        pdf.seek(0)
        reader = PdfReader(pdf)

        # Navigate /Root/Names/EmbeddedFiles/Names
        root = reader.trailer.get("/Root")
        names_dict = root.get("/Names") if root else None
        embedded = names_dict.get("/EmbeddedFiles") if names_dict else None
        names_array = embedded.get_object().get("/Names") if embedded else None

        if not names_array:
            return render(
                request,
                "core/extract.html",
                {"form": form, "error": "This PDF does not contain embedded attachments."},
                status=400,
            )

        out_zip = BytesIO()
        with ZipFile(out_zip, "w") as zf:
            for i in range(0, len(names_array), 2):
                try:
                    name_obj = str(names_array[i])
                    filespec = names_array[i + 1].get_object()
                    ef = filespec.get("/EF")
                    f_stream = ef.get("/F").get_object() if ef else None
                    data = f_stream.get_data() if f_stream else b""
                    zf.writestr(safe_name(name_obj), data)
                except Exception:
                    # skip broken entries but continue with others
                    continue

        out_zip.seek(0)
        stem = pdf.name.rsplit(".", 1)[0]
        return FileResponse(
            out_zip,
            as_attachment=True,
            filename=f"{safe_name(stem)}_attachments.zip",
            content_type="application/zip",
        )

    except Exception as e:
        return render(
            request,
            "core/extract.html",
            {"form": form, "error": f"An error occurred: {e}"},
            status=500,
        )
