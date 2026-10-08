import streamlit as st

st.set_page_config(page_title="Song Generator", page_icon="🎵")

st.title("🎵 Song Generator")
st.write("Choose a style and topic to get started.")

genre = st.selectbox("Genre", ["Pop", "Rock", "Hip-hop", "Country", "R&B"])
mood = st.selectbox("Mood", ["Uplifting", "Chill", "Heartfelt", "Energetic"])
topic = st.text_input("What should the song be about?")

if st.button("Generate song"):
    if topic.strip():
        st.success("Your song settings are ready!")
        st.write(f"**Genre:** {genre}")
        st.write(f"**Mood:** {mood}")
        st.write(f"**Topic:** {topic}")
    else:
        st.warning("Enter a topic first.")
