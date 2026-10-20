"""CodeAlpha AI Internship - Task 1: Language Translation Tool
Streamlit UI + Google Translate (via deep-translator) + gTTS text-to-speech + copy button.
Run:  streamlit run app.py
"""
import io
import json
import time

import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator, MyMemoryTranslator
from deep_translator.exceptions import TooManyRequests
from gtts import gTTS

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐", layout="centered")

# {display name: code}
LANGUAGES = {"Auto-detect": "auto", **{name.title(): code
             for name, code in GoogleTranslator().get_supported_languages(as_dict=True).items()}}
TARGETS = {k: v for k, v in LANGUAGES.items() if k != "Auto-detect"}


# MyMemory uses region codes (e.g. "ur-PK"); map short Google codes (e.g. "ur") onto them
_MM_CODES = {}
for _c in MyMemoryTranslator(source="en-GB", target="ur-PK").get_supported_languages(as_dict=True).values():
    _MM_CODES.setdefault(_c.split("-")[0].lower(), _c)
_MM_CODES.update({"zh-CN": "zh-CN", "zh-TW": "zh-TW", "en": "en-GB"})


def _mm(code: str) -> str:
    return code if code == "auto" else _MM_CODES.get(code, code)


def translate(text: str, source: str, target: str) -> str:
    """Try Google Translate first; if it rate-limits us, fall back to MyMemory (also free)."""
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except TooManyRequests:
        time.sleep(2)  # short pause, then retry once
        try:
            return GoogleTranslator(source=source, target=target).translate(text)
        except TooManyRequests:
            st.info("Google rate-limited this connection, so MyMemory was used instead.")
            return MyMemoryTranslator(source=_mm(source), target=_mm(target)).translate(text)


def speak(text: str, lang: str) -> bytes:
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


def copy_button(text: str) -> None:
    components.html(
        f"""<button onclick='navigator.clipboard.writeText({json.dumps(text)}).then(()=>
        {{this.innerText="Copied!"}})' style="padding:8px 16px;border-radius:6px;
        border:1px solid #888;cursor:pointer;font-size:14px">📋 Copy</button>""",
        height=50,
    )


st.title("🌐 Language Translation Tool")
st.caption("CodeAlpha AI Internship – Task 1")

text = st.text_area("Enter text to translate", height=150, placeholder="Type or paste text here...")
c1, c2 = st.columns(2)
src = c1.selectbox("From", list(LANGUAGES), index=0)
tgt = c2.selectbox("To", list(TARGETS), index=list(TARGETS).index("Urdu") if "Urdu" in TARGETS else 0)

if st.button("Translate", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        try:
            with st.spinner("Translating..."):
                st.session_state["result"] = translate(text, LANGUAGES[src], TARGETS[tgt])
                st.session_state["tgt_code"] = TARGETS[tgt]
        except Exception as e:  # network / API errors
            st.error(f"Translation failed: {e}")

if "result" in st.session_state:
    st.subheader("Translation")
    st.success(st.session_state["result"])
    copy_button(st.session_state["result"])
    if st.button("🔊 Listen"):
        try:
            st.audio(speak(st.session_state["result"], st.session_state["tgt_code"]), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech not available for this language: {e}")