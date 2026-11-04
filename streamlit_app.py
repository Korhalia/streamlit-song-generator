import logging
import re

import streamlit as st
from openai import OpenAI
from elevenlabs.client import ElevenLabs


# Keep detailed errors in the server logs, not on the public app page.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4.1-mini"
ELEVENLABS_MODEL = "music_v2_5"
MAX_TOPIC_LENGTH = 300


def get_secret(name: str) -> str:
    """Return a configured Streamlit secret, or an empty string if missing."""
    try:
        return str(st.secrets[name]).strip()
    except (KeyError, FileNotFoundError):
        return ""


def split_lyrics_into_sections(lyrics: str) -> list[dict[str, str]]:
    """Split bracket-labeled lyrics into sections for ElevenLabs."""
    sections = []
    current_label = None
    current_lines = []

    def save_current_section():
        if current_label and current_lines:
            text = "\n".join(current_lines).strip()
            # A title is for display, not a sung section.
            if text and current_label.strip().lower() != "title":
                sections.append({"label": current_label.strip(), "lyrics": text})

    for line in lyrics.splitlines():
        heading = re.match(r"^\s*\[([^\]]+)\]\s*$", line)

        if heading:
            save_current_section()
            current_label = heading.group(1).strip()
            current_lines = []
        elif current_label:
            current_lines.append(line)

    save_current_section()

    # If the lyrics weren't returned with recognized headings, use them as
    # one section rather than dropping the text.
    if not sections:
        sections = [{"label": "Full Song", "lyrics": lyrics.strip()}]

    return sections


def make_composition_plan(
    lyrics: str,
    genre: str,
    mood: str,
    song_length_seconds: int,
) -> dict:
    """Create a documented ElevenLabs Music v2.5 composition plan."""
    sections = split_lyrics_into_sections(lyrics)
    total_ms = song_length_seconds * 1000

    # Each composition-plan chunk must be at least 3 seconds.
    if len(sections) * 3000 > total_ms:
        sections = [{"label": "Full Song", "lyrics": lyrics.strip()}]

    base_duration_ms = total_ms // len(sections)
    extra_ms = total_ms % len(sections)

    styles = [
        f"{genre} music",
        f"{mood.lower()} mood",
        "sung vocals",
        "clear vocal delivery",
        "catchy melody",
        "original song",
        "polished studio production",
    ]

    chunks = []
    for index, section in enumerate(sections):
        duration_ms = base_duration_ms
        if index < extra_ms:
            duration_ms += 1

        chunks.append(
            {
                "text": f"[{section['label']}]\n{section['lyrics']}",
                "duration_ms": duration_ms,
                "positive_styles": styles,
                "negative_styles": [],
                "context_adherence": "high",
            }
        )

    return {"chunks": chunks}


st.set_page_config(page_title="Sonnetide", page_icon="🎵"
)
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at top left, #39235f 0%, transparent 45%),
            linear-gradient(135deg, #11111c 0%, #191529 55%, #10131d 100%);
        color: #f8f7fc;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    .hero-card {
        padding: 3rem 2rem;
        margin: 1rem 0 2rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 24px;
        background: linear-gradient(
            135deg,
            rgba(124, 58, 237, 0.34),
            rgba(236, 72, 153, 0.15),
            rgba(18, 18, 31, 0.8)
        );
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.25);
    }

    .hero-kicker {
        color: #d8b4fe;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .hero-title {
        margin: 0.7rem 0;
        color: #ffffff;
        font-size: clamp(2.4rem, 7vw, 4.5rem);
        font-weight: 800;
        line-height: 1.05;
    }

    .hero-copy {
    max-width: 620px;
    margin: 0 auto 1.6rem;
    color: #a0a4d0;
    font-size: 1.1rem;
    line-height: 1.6;
    text-align: center;
}

    }

    .hero-button {
        display: inline-block;
        padding: 0.85rem 1.4rem;
        border-radius: 999px;
        background: linear-gradient(90deg, #a855f7, #ec4899);
        color: white !important;
        font-weight: 700;
        text-decoration: none !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .hero-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.35);
    }

    @media (max-width: 600px) {
        .hero-card {
            padding: 2.2rem 1.2rem;
        }

        .hero-copy {
            font-size: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

import textwrap  # Add this near the other imports at the top of the file

st.markdown(
    """
    <section class="hero-card">
        <div class="hero-kicker">Your idea. Your sound.</div>
        <h1>Create a song out of it</h1>
        <p class="hero-copy" style="text-align: center; max-width: 620px; margin: 12px auto 20px;">
            Pick a mood, choose a style, and turn your idea into an original song with custom lyrics.
        </p>
        <a class="hero-button" href="#song-controls">Create Your Song</a>
    </section>
    """,
    unsafe_allow_html=True,
)




st.title("♫ Sonnetide")

st.caption("Create original lyrics, then turn them into a sung song.")

openai_key = get_secret("OPENAI_API_KEY")
elevenlabs_key = get_secret("ELEVENLABS_API_KEY")

genre = st.selectbox(
    "Choose a genre",
    ["Pop", "Country", "R&B", "Rock", "Gospel", "Hip-hop"],
)
mood = st.selectbox(
    "Choose a mood",
    ["Happy", "Romantic", "Hopeful", "Sad", "Energetic", "Relaxed"],
)
topic = st.text_input(
    "What should the song be about?",
    max_chars=MAX_TOPIC_LENGTH,
)
song_length_seconds = st.selectbox(
    "Song length",
    [30, 60, 90, 120],
    index=1,
    format_func=lambda seconds: f"{seconds} seconds",
)

current_context = (genre, mood, topic.strip())

if st.button("Generate lyrics"):
    if not openai_key:
        st.error("Add OPENAI_API_KEY to your Streamlit app's Secrets.")
    elif not topic.strip():
        st.warning("Enter a topic for your song first.")
    else:
        try:
            client = OpenAI(api_key=openai_key)

            with st.spinner("Writing your lyrics..."):
                response = client.responses.create(
                    model=OPENAI_MODEL,
                    instructions=(
                        "Write original song lyrics. Do not imitate a specific "
                        "artist or include existing copyrighted lyrics. Return "
                        "a title followed by these clearly labeled sections: "
                        "[Verse 1], [Chorus], [Verse 2], [Chorus], [Bridge], "
                        "and [Final Chorus]. Do not use Markdown code fences."
                    ),
                    input=(
                        f"Genre: {genre}\n"
                        f"Mood: {mood}\n"
                        f"Topic: {topic.strip()}"
                    ),
                )

            lyrics = (response.output_text or "").strip()
            if not lyrics:
                st.error("The lyrics service returned an empty result.")
            else:
                st.session_state["lyrics"] = lyrics
                st.session_state["lyrics_context"] = current_context
                # Clear an old song so it isn't mistaken for the new lyrics.
                st.session_state.pop("audio_bytes", None)

        except Exception:
            logger.exception("Lyrics generation failed")
            st.error(
                "Lyrics could not be generated. Check your OpenAI API key "
                "and account, then try again."
            )

lyrics = st.session_state.get("lyrics", "")
lyrics_context = st.session_state.get("lyrics_context")
lyrics_match_current_choices = lyrics_context == current_context

if lyrics:
    st.subheader("Your lyrics")

    if not lyrics_match_current_choices:
        st.warning(
            "These lyrics were made with different choices. Generate new "
            "lyrics before creating a song."
        )

    st.text(lyrics)
    st.download_button(
        "Download lyrics",
        data=lyrics,
        file_name="song_lyrics.txt",
        mime="text/plain",
    )

if st.button("Generate full song"):
    if not elevenlabs_key:
        st.error("Add ELEVENLABS_API_KEY to your Streamlit app's Secrets.")
    elif not topic.strip():
        st.warning("Enter a topic for your song first.")
    elif not lyrics:
        st.warning("Generate lyrics before creating the full song.")
    elif not lyrics_match_current_choices:
        st.warning("Generate fresh lyrics for your current genre, mood, and topic.")
    else:
        try:
            client = ElevenLabs(api_key=elevenlabs_key)
            composition_plan = make_composition_plan(
                lyrics=lyrics,
                genre=genre,
                mood=mood,
                song_length_seconds=song_length_seconds,
            )

            with st.spinner(
                "Generating your song. This can take a little while..."
            ):
                audio_chunks = client.music.compose(
                    composition_plan=composition_plan,
                    model_id=ELEVENLABS_MODEL,
                )
                audio_bytes = b"".join(audio_chunks)

            if not audio_bytes:
                raise RuntimeError("The music service returned no audio.")

            st.session_state["audio_bytes"] = audio_bytes

        except Exception:
            logger.exception("Song generation failed")
            st.error(
                "Song generation failed. Check your ElevenLabs key, account "
                "access, and server logs, then try again."
            )

audio_bytes = st.session_state.get("audio_bytes")
if audio_bytes:
    st.subheader("Your song")
    st.audio(audio_bytes, format="audio/mpeg")
    st.download_button(
        "Download song",
        data=audio_bytes,
        file_name="song.mp3",
        mime="audio/mpeg",
    )
    st.caption(
        "The music model may not reproduce every lyric exactly as written."
    )
    st.markdown("---")
st.header("Pricing")
st.caption("Choose the plan that fits your creative flow.")

free, creator, studio = st.columns(3)

with free:
    st.subheader("Free")
    st.markdown("## $0")
    st.write("2 songs per month")
    st.write("Create original lyrics")
    st.button("Get started", key="free_plan", use_container_width=True)

with creator:
    st.subheader("Creator")
    st.markdown("## $9 / month")
    st.write("25 songs per month")
    st.write("Create and listen to your songs")
    st.button("Choose Creator", key="creator_plan", use_container_width=True)

with studio:
    st.subheader("Studio") 
    st.markdown(
    """
    <style>
    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button,
    .stLinkButton > a,
    a[class*="button"] {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border: 1px solid #a78bfa !important;
        border-radius: 10px !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover,
    .stLinkButton > a:hover,
    a[class*="button"]:hover {
        background-color: #6d28d9 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    st.markdown("## $19 / month")
    st.write("75 songs per month")
    st.write("For frequent song creators")
    st.button("Choose Studio", key="studio_plan", use_container_width=True)
