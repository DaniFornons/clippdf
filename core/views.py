from io import BytesIO
import unicodedata
from zipfile import ZipFile
from pathlib import Path 

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import render, redirect

from pypdf import PdfReader, PdfWriter

from .forms import AddAttachmentsForm, ExtractForm

def safe_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return (name or "attachment").replace(" ", "_")

def home(request):
    return render(request, "core/home.html")

def generate(request):
    if request.method == "GET":
        return render(request, "core/add.html", {"form": AddAttachmentsForm()})

    # POST
    form = AddAttachmentsForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "core/add.html", {"form": form}, status=400)

    pdf_base = form.cleaned_data["pdf_base"]
    attachments = request.FILES.getlist("attachments")

    if not attachments:
        messages.error(request, "Si us plau, seleccioneu almenys un fitxer per adjuntar.")
        return redirect("core:generate")
    
    valid_extensions = {
        '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
        '.odt', '.ods', '.odp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'
    }
    for attachment in attachments:
        ext = Path(attachment.name).suffix.lower()
        if ext not in valid_extensions:
            messages.error(request, f"Tipus d'arxiu no permès: {ext}")
            return redirect("core:generate")
    
    try:
        pdf_base.seek(0)
        reader = PdfReader(pdf_base)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        used = set()

        def unique(n):
            base, dot, ext = n.rpartition(".")
            cand, i = n, 1
            while cand in used:
                cand = f"{base}_{i}.{ext}" if ext else f"{n}_{i}"
                i += 1
            used.add(cand)
            return cand

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
            filename=f"{safe_name(stem)}_amb_adjunts.pdf",
            content_type="application/pdf",
        )
    except Exception as e:
        messages.error(request, ("Error inesperat: %(msg)s") % {"msg": e})
        return redirect("core:generate")

def extract(request):
    if request.method == "GET":
        return render(request, "core/extract.html", {"form": ExtractForm()})

    # POST
    form = ExtractForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "core/extract.html", {"form": form}, status=400)

    pdf = form.cleaned_data["pdf_with_attachments"]

    try:
        pdf.seek(0)
        reader = PdfReader(pdf)

        root = reader.trailer.get("/Root")
        names_dict = root.get("/Names") if root else None
        embedded = names_dict.get("/EmbeddedFiles") if names_dict else None
        names_array = embedded.get_object().get("/Names") if embedded else None

        if not names_array:
            messages.warning(request, "Aquest PDF no conté fitxers adjunts.")
            return redirect("core:extract")  # PRG
 
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
                    continue

        out_zip.seek(0)
        stem = pdf.name.rsplit(".", 1)[0]
        return FileResponse(
            out_zip,
            as_attachment=True,
            filename=f"{safe_name(stem)}_adjunts.zip",
            content_type="application/zip",
        )
    except Exception as e:
        messages.error(request, f"Error inesperat: {e}")
        return redirect("core:extract")
