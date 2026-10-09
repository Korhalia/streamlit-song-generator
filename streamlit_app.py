import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Song Generator", page_icon="🎵")
st.title("🎵 Song Generator")

try:
    openai_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_key = ""

genre = st.selectbox(
    "Choose a genre",
    ["Pop", "Country", "R&B", "Rock", "Gospel", "Hip-hop"]
)
mood = st.selectbox(
    "Choose a mood",
    ["Happy", "Romantic", "Hopeful", "Sad", "Energetic", "Relaxed"]
)
topic = st.text_input("What should the song be about?")

if st.button("Generate lyrics"):
    if not openai_key:
        st.error("Add OPENAI_API_KEY to your Streamlit app's Secrets first.")
    elif not topic.strip():
        st.warning("Enter a topic for your song first.")
    else:
        try:
            client = OpenAI(api_key=openai_key)

            with st.spinner("Writing your lyrics..."):
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions=(
                        "Write original song lyrics. Include a title, "
                        "verses, a catchy chorus, and a bridge."
                    ),
                    input=f"Genre: {genre}\nMood: {mood}\nTopic: {topic}"
                )

            st.session_state["lyrics"] = response.output_text

        except Exception as error:
            st.error(f"Lyrics could not be generated. Check your API key and try again. Details: {error}")

if st.session_state.get("lyrics"):
    st.subheader("Your lyrics")
    st.write(st.session_state["lyrics"])
    st.download_button(
        "Download lyrics",
        st.session_state["lyrics"],
        file_name="song_lyrics.txt"
    )

if st.button("Generate full song"):
    st.info(
        "This button is on the app, but audio generation still needs to be "
        "connected to a music-generation service. The OpenAI key used above "
        "generates lyrics; it does not by itself create a complete sung song."
    )
