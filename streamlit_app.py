import streamlit as st
import subprocess
import json
import os
import tempfile
from datetime import datetime
import mimetypes

# Grupe/tag-uri pe care nu are sens să încercăm să le scriem
NON_WRITABLE_GROUPS = {"File", "System", "Composite"}
ALWAYS_SKIP_TAGS = {"SourceFile", "Directory", "FileName"}
RESERVED_TAGS = {
    "Title",
    "XPTitle",
    "ObjectName",
    "Artist",
    "XPAuthor",
    "Creator",
    "ImageDescription",
    "XPComment",
    "Description",
    "Keywords",
    "Copyright",
    "DateTimeOriginal",
    "CreateDate",
    "ModifyDate",
}


def find_first_tag(meta: dict, tag_names):
    """Caută primul tag din listă (ignorând grupul)."""
    for key, value in meta.items():
        if ":" in key:
            _, t = key.split(":", 1)
        else:
            t = key
        if t in tag_names:
            return value
    return None


def read_metadata(filepath: str) -> dict:
    """Returnează meta datele ca dict folosind exiftool."""
    result = subprocess.run(
        ["exiftool", "-G1", "-j", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Eroare necunoscută la exiftool")
    data = json.loads(result.stdout)
    if not data:
        return {}
    return data[0]


def build_exiftool_cmd_from_fields(
    title: str,
    author: str,
    desc: str,
    keywords: str,
    copyright_text: str,
    date_original: str,
    raw_meta: str,
    apply_raw: bool,
):
    """Construiește lista cu argumente pentru exiftool."""
    cmd = []

    # Câmpuri standard
    if title:
        cmd.append(f"-Title={title}")
        cmd.append(f"-XPTitle={title}")
        cmd.append(f"-ObjectName={title}")

    if author:
        cmd.append(f"-Artist={author}")
        cmd.append(f"-XPAuthor={author}")
        cmd.append(f"-Creator={author}")

    if desc:
        cmd.append(f"-ImageDescription={desc}")
        cmd.append(f"-XPComment={desc}")
        cmd.append(f"-Description={desc}")

    if keywords:
        cmd.append("-Keywords=")  # golim mai întâi
        for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
            cmd.append(f"-Keywords={kw}")

    if copyright_text:
        cmd.append(f"-Copyright={copyright_text}")

    if date_original:
        cmd.append(f"-DateTimeOriginal={date_original}")

    # Meta completă (avansat)
    if apply_raw and raw_meta:
        for line in raw_meta.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key_raw, value = line.split("=", 1)
            key_raw = key_raw.strip()
            value = value.strip()

            if not key_raw:
                continue

            if ":" in key_raw:
                group, tag_name = key_raw.split(":", 1)
                group = group.strip()
                tag_name = tag_name.strip()
            else:
                group = None
                tag_name = key_raw

            # filtrăm ce nu vrem să atingem
            if tag_name in ALWAYS_SKIP_TAGS:
                continue
            if tag_name in RESERVED_TAGS:
                continue
            if group in NON_WRITABLE_GROUPS:
                continue

            exiftool_tag = key_raw  # păstrăm și grupul dacă există

            if value == "":
                cmd.append(f"-{exiftool_tag}=")
            else:
                cmd.append(f"-{exiftool_tag}={value}")

    return cmd


# ---------------------- UI STREAMLIT ----------------------

st.set_page_config(page_title="Meta Image Editor", layout="wide")

st.title("🖼️ Image Metadata Editor (Streamlit)")
st.write(
    "Încarcă una sau mai multe imagini, vezi meta datele și rescrie-le folosind ExifTool."
)

uploaded_files = st.file_uploader(
    "Încarcă imagini",
    type=["jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif", "heic", "webp"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Încarcă cel puțin o imagine pentru a începe.")
    st.stop()

# director temporar în sesiune
if "tempdir" not in st.session_state:
    st.session_state["tempdir"] = tempfile.mkdtemp()

tempdir = st.session_state["tempdir"]

# salvăm fișierele încărcate
paths = []
for uf in uploaded_files:
    path = os.path.join(tempdir, uf.name)
    with open(path, "wb") as f:
        f.write(uf.read())
    paths.append(path)

# fișier curent pentru inspectarea meta datelor
idx = 0
if len(paths) > 1:
    idx = st.selectbox(
        "Alege fișier pentru vizualizarea meta datelor",
        options=list(range(len(paths))),
        format_func=lambda i: os.path.basename(paths[i]),
    )

current_path = paths[idx]
st.write(f"**Fișier curent:** `{os.path.basename(current_path)}`")

try:
    meta = read_metadata(current_path)
except Exception as e:
    st.error(f"Eroare la citirea meta datelor cu exiftool: {e}")
    st.stop()

# inițializăm câmpurile când se schimbă fișierul curent
if "current_file" not in st.session_state or st.session_state["current_file"] != current_path:
    st.session_state["current_file"] = current_path

    title = find_first_tag(meta, ["Title", "ObjectName", "XPTitle"]) or ""
    author = find_first_tag(meta, ["Artist", "Creator", "XPAuthor"]) or ""
    desc = find_first_tag(meta, ["Description", "ImageDescription", "XPComment"]) or ""
    kws = find_first_tag(meta, ["Keywords"])
    if isinstance(kws, list):
        kws = ", ".join(str(k) for k in kws)
    keywords = kws or ""
    copyright_text = find_first_tag(meta, ["Copyright"]) or ""
    date_original = (
        find_first_tag(meta, ["DateTimeOriginal"])
        or find_first_tag(meta, ["CreateDate"])
        or find_first_tag(meta, ["ModifyDate"])
        or ""
    )

    st.session_state["title"] = title
    st.session_state["author"] = author
    st.session_state["desc"] = desc
    st.session_state["keywords"] = keywords
    st.session_state["copyright"] = copyright_text
    # aici folosim o cheie separată pentru input-ul de dată
    st.session_state["date_original_input"] = date_original

    # meta completă text (editabilă)
    lines = []
    for tag in sorted(meta.keys()):
        value = meta[tag]
        lines.append(f"{tag} = {value}")
    st.session_state["raw_meta"] = "\n".join(lines)

# callback pentru butonul „Data curentă”
def set_current_date():
    st.session_state["date_original_input"] = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

# layout pe două coloane
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Meta standard (se aplică la toate fișierele încărcate)")

    st.text_input(
        "Titlu (ex: „Gresie porțelanată 60x60”)",
        key="title",
    )

    st.text_input(
        "Autor (ex: „CeraMall Studio”)",
        key="author",
    )

    st.text_input(
        "Descriere (ex: „Fotografie produs pentru site”)",
        key="desc",
    )

    st.text_input(
        "Keywords (separate prin virgulă, ex: „gresie, faianta, parchet, baie”)",
        key="keywords",
    )

    st.text_input(
        'Copyright (ex: "© 2025 CeraMall")',
        key="copyright",
    )

    date_col1, date_col2 = st.columns([2, 1])
    with date_col1:
        st.text_input(
            "Data originală (YYYY:MM:DD HH:MM:SS, ex: 2025:12:02 10:15:00)",
            key="date_original_input",
        )
    with date_col2:
        st.button("Data curentă", on_click=set_current_date)

with col2:
    st.subheader("Meta completă (editabilă – avansat)")
    st.write(
        "Format: `Grup:Tag = valoare` (o meta pe linie). "
        "Tag-urile de fișier (File/System/Composite) sunt ignorate automat.\n"
        "Tot ce scrii aici este aplicat în fișiere dacă bifezi checkbox-ul de mai jos."
    )
    st.text_area(
        "Editează meta datele brute",
        key="raw_meta",
        height=300,
    )
    st.checkbox(
        "Aplică și modificările din meta completă",
        key="apply_raw",
        value=False,
    )

st.markdown("---")

# buton de scriere în fișiere
if st.button("✏️ Scrie meta date în toate fișierele încărcate"):
    title = st.session_state.get("title", "").strip()
    author = st.session_state.get("author", "").strip()
    desc = st.session_state.get("desc", "").strip()
    keywords = st.session_state.get("keywords", "").strip()
    copyright_text = st.session_state.get("copyright", "").strip()
    date_original = st.session_state.get("date_original_input", "").strip()
    raw_meta = st.session_state.get("raw_meta", "")
    apply_raw = st.session_state.get("apply_raw", False)

    if (
        not any([title, author, desc, keywords, copyright_text, date_original])
        and not apply_raw
    ):
        st.warning(
            "Nu ai completat niciun câmp și nu ai bifat aplicarea meta-ului complet. "
            "Nu am ce să scriu în fișiere."
        )
        st.stop()

    base_cmd = build_exiftool_cmd_from_fields(
        title,
        author,
        desc,
        keywords,
        copyright_text,
        date_original,
        raw_meta,
        apply_raw,
    )

    if not base_cmd:
        st.warning("Niciun tag de rescris. Verifică datele introduse.")
        st.stop()

    cmd = ["exiftool"] + base_cmd + ["-overwrite_original"] + paths

    st.code(" ".join(cmd), language="bash")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        st.error(
            "Nu am găsit `exiftool` în mediu. "
            "Pe Streamlit Cloud ai nevoie de un fișier `packages.txt` cu o linie:\n\n`exiftool`"
        )
        st.stop()

    if result.returncode != 0:
        st.error(
            "Eroare la rularea exiftool:\n\n"
            + (result.stderr or "Eroare necunoscută.")
        )
    else:
        st.success("Meta datele au fost actualizate cu succes pentru toate fișierele încărcate!")

        st.subheader("Descarcă fișierele modificate")
        for p in paths:
            if not os.path.exists(p):
                continue
            with open(p, "rb") as f:
                data = f.read()
            mime, _ = mimetypes.guess_type(p)
            if mime is None:
                mime = "application/octet-stream"
            st.download_button(
                label=f"Descarcă {os.path.basename(p)}",
                data=data,
                file_name=os.path.basename(p),
                mime=mime,
            )
