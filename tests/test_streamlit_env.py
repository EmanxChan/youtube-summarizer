import os
import streamlit as st

st.title("🔧 Environment Variable Test")

st.write("### Listen Notes API Credentials Check")

api_key = os.getenv('LISTEN_NOTES_API_KEY')

if api_key:
    st.success(f"✓ LISTEN_NOTES_API_KEY: {api_key[:20]}...")
else:
    st.error("❌ LISTEN_NOTES_API_KEY not set")

if api_key:
    st.write("---")
    st.write("### Test Listen Notes Client")
    
    try:
        from listen_notes_client import ListenNotesClient
        client = ListenNotesClient()
        st.success("✓ ListenNotesClient initialized successfully!")
        
        # Quick test
        if st.button("Test Search for 'The Daily'"):
            with st.spinner("Searching..."):
                results = client.search_podcast('The Daily', limit=3)
                if results:
                    st.success(f"✓ Found {len(results)} podcast(s)")
                    for podcast in results:
                        st.write(f"- {podcast['title']} ({podcast['total_episodes']} episodes)")
                else:
                    st.warning("⚠️ No podcasts found")
    except Exception as e:
        st.error(f"❌ Error: {e}")
