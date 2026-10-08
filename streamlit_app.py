import streamlit as st
from openai import OpenAI

st.title("🎵 Song Lyric Generator")
st.write("Choose a style and enter a topic to create original lyrics.")

genre = st.selectbox(
    "Genre",
    ["Pop", "Rock", "Country", "Hip-hop", "R&B", "Folk"]
)

mood = st.selectbox(
    "Mood",
    ["Happy", "Romantic", "Hopeful", "Sad", "Energetic", "Chill"]
)

topic = st.text_input("What should the song be about?")

if st.button("Generate lyrics"):
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            st.error("Add OPENAI_API_KEY in your Streamlit app's Secrets settings.")
        else:
            prompt = f"""
Write original song lyrics in the {genre} genre with a {mood} mood.
The song should be about: {topic}

Include a title, two verses, and a catchy chorus.
Do not include audio or music instructions.
"""

            try:
                client = OpenAI(api_key=api_key)

                with st.spinner("Writing your lyrics..."):
                    response = client.responses.create(
                        model="gpt-5-mini",
                        input=prompt
                    )

                st.subheader("Your lyrics")
                st.markdown(response.output_text)

            except Exception as error:
                st.error(f"Something went wrong: {error}")
