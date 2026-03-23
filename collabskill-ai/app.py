st.markdown("""
<style>
.stApp {
    background-color: #050816;
}

/* REMOVE HEADER */
header {visibility:hidden;}
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

/* HERO TEXT */
.hero {
    text-align: center;
    margin-top: 80px;
}

.hero h1 {
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
}

/* FIX VISIBILITY */
.light-text {
    color: #e5e7eb;  /* brighter white */
}

/* GRADIENT */
.gradient {
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">

    <h1 class="light-text">
        Connect.<br>
        Collaborate.
    </h1>

    <h1 class="gradient">
        Exchange Skills
    </h1>

    <h1 class="gradient">
        Smarter.
    </h1>

</div>
""", unsafe_allow_html=True)
