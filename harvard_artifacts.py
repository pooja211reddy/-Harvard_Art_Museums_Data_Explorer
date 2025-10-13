import streamlit as st
import requests
import mysql.connector


# 🔑 API & DB Setup
API_KEY = "8f48cd3f-1882-4cf0-93ed-a0745c2b678a"
BASE_URL = "https://api.harvardartmuseums.org/object"
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Doordie123',
    'database': 'harvard_art'
}

import streamlit as st

# ✅ Enable HTML rendering
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <div style="text-align:center; padding:20px 0;">
        <h1 style="font-family:'Poppins',sans-serif; font-weight:700; font-size:42px; color:#1e3a8a; margin-bottom:10px;">
            <i class="fa-solid fa-landmark" style="color:#1e3a8a;"></i>
            &nbsp; Harvard Art Museums 
            <span style="color:#7c3aed;">Data Explorer</span>
            &nbsp;<i class="fa-solid fa-palette" style="color:#7c3aed;"></i>
        </h1>
        <p style="font-size:17px; color:#475569; margin-top:-5px;">
            <i class="fa-solid fa-database" style="color:#2563eb;"></i>
            &nbsp; Powered by Harvard API · MySQL · Streamlit &nbsp;
            <i class="fa-solid fa-chart-line" style="color:#22c55e;"></i>
        </p>
    </div>
""", unsafe_allow_html=True)




page_bg = """
<style>
/* ===== Main Page Background ===== */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
    color: #1e293b;
}

/* ===== Sidebar Styling ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    border-right: 2px solid #64748b;
}

[data-testid="stSidebar"] * {
    color: #f1f5f9 !important;
    font-size: 15px !important;
}

/* ===== Headings & Text ===== */
h1, h2, h3 {
    color: #1e293b;
    font-weight: 700;
    letter-spacing: 0.5px;
}

h1 {
    color: #0f172a;
    background: -webkit-linear-gradient(90deg, #334155, #1e3a8a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

h2 {
    color: #1e293b;
}

[data-testid="stHeader"] {
    background: rgba(255,255,255,0.4);
    backdrop-filter: blur(5px);
}

/* ===== Buttons ===== */
.stButton>button {
    background: linear-gradient(90deg, #3b82f6, #6366f1);
    color: white;
    border: none;
    padding: 0.6em 1.2em;
    border-radius: 8px;
    font-weight: 600;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: translateY(-2px);
    background: linear-gradient(90deg, #2563eb, #4f46e5);
}

/* ===== Info Boxes ===== */
div[data-testid="stAlert"] {
    border-radius: 10px;
    font-size: 15px;
}

/* ===== Tabs Styling ===== */
[data-baseweb="tab-list"] {
    background-color: #f8fafc;
    border-radius: 8px;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)


# ⚙️ MySQL Connection
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

# ✅ Create tables if not exist
def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artifact_metadata (
            id INT PRIMARY KEY,
            title TEXT,
            culture TEXT,
            period TEXT,
            century TEXT,
            medium TEXT,
            dimensions TEXT,
            description TEXT,
            department TEXT,
            classification TEXT,
            accessionyear INT,
            accessionmethod TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artifact_media (
            objectid INT,
            imagecount INT,
            mediacount INT,
            colorcount INT,
            `rank` FLOAT,
            datebegin INT,
            dateend INT,
            FOREIGN KEY (objectid) REFERENCES artifact_metadata(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artifact_colors (
            objectid INT,
            color TEXT,
            spectrum TEXT,
            hue TEXT,
            percent FLOAT,
            css3 TEXT,
            FOREIGN KEY (objectid) REFERENCES artifact_metadata(id)
        )
    """)
    conn.commit()
    conn.close()

# 🎨 Fetch classifications dynamically (only ≥ 2500 records)
@st.cache_data(show_spinner=False)
def get_classifications():
    url = "https://api.harvardartmuseums.org/classification"
    params = {"apikey": API_KEY, "size": 100}
    response = requests.get(url, params=params)
    data = response.json()
    return [
        rec["name"] for rec in data.get("records", [])
        if rec.get("objectcount", 0) >= 2500
    ]

# 📦 Fetch artifact data for chosen classification
def fetch_artifacts(classification):
    objects, page = [], 1
    st.info(f"Fetching up to 2500 records for '{classification}'...")
    while len(objects) < 2500:
        resp = requests.get(BASE_URL, params={
            "apikey": API_KEY,
            "size": 100,
            "page": page,
            "classification": classification
        })
        data = resp.json()
        recs = data.get("records", [])
        if not recs:
            break
        objects.extend(recs)
        page += 1
    return objects[:2500]

# 💾 Insert data into MySQL directly
def insert_into_mysql(records, classification):
    conn = connect_db()
    cur = conn.cursor()

    # avoid duplicate classification
    cur.execute("SELECT DISTINCT classification FROM artifact_metadata")
    existing = [c[0].lower() for c in cur.fetchall()]
    if classification.lower() in existing:
        st.warning("⚠️ Classification already exists in database.")
        conn.close()
        return

    meta_rows, media_rows, color_rows = [], [], []
    for r in records:
        meta_rows.append((
            r.get("id"), r.get("title"), r.get("culture"), r.get("period"),
            r.get("century"), r.get("medium"), r.get("dimensions"),
            r.get("description"), r.get("department"), r.get("classification"),
            r.get("accessionyear"), r.get("accessionmethod")
        ))
        media_rows.append((
            r.get("id"), r.get("imagecount"), r.get("mediacount"),
            r.get("colorcount"), r.get("rank"), r.get("datebegin"), r.get("dateend")
        ))
        if r.get("colors"):
            for c in r["colors"]:
                color_rows.append((
                    r.get("id"), c.get("color"), c.get("spectrum"),
                    c.get("hue"), c.get("percent"), c.get("css3")
                ))

    cur.executemany("""
        INSERT INTO artifact_metadata
        (id, title, culture, period, century, medium, dimensions,
         description, department, classification, accessionyear, accessionmethod)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, meta_rows)

    cur.executemany("""
        INSERT INTO artifact_media
        (objectid, imagecount, mediacount, colorcount, `rank`, datebegin, dateend)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, media_rows)

    cur.executemany("""
        INSERT INTO artifact_colors
        (objectid, color, spectrum, hue, percent, css3)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, color_rows)
    st.success(f"✅ Inserted {len(records)} records successfully!")
    tab1, tab2, tab3 = st.tabs(["📋 Metadata", "🖼️ Media", "🌈 Colors"])
    with tab1:
        cur.execute(f"SELECT * FROM artifact_metadata WHERE classification = %s ;", (classification,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        st.dataframe([dict(zip(cols, r)) for r in rows])
    with tab2:
        cur.execute("SELECT * FROM artifact_media ORDER BY objectid DESC ;")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        st.dataframe([dict(zip(cols, r)) for r in rows])
    with tab3:
        cur.execute("SELECT * FROM artifact_colors ORDER BY objectid DESC ;")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        st.dataframe([dict(zip(cols, r)) for r in rows])

    conn.commit()
    conn.close()
    

# 🧮 Run a query with pure MySQL connector
def run_query(query):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    conn.close()
    return headers, rows


# ---------- SIDEBAR NAVIGATION ----------
st.sidebar.title("📚 Navigation Menu")
page = st.sidebar.radio(
    "Go to section:",
    ["1️⃣ Introduction", "2️⃣ Fetch Data", "3️⃣ Insert Data", "4️⃣ Query Explorer", "5️⃣ Creator Info"]
)

create_tables()

# ---------- 1️⃣ INTRODUCTION ----------
if page.startswith("1️⃣"):
    st.header(" Overview ")
    st.markdown("""
     
    This app lets you:
    - Fetch real artifact data from the **Harvard Art Museums API**
    - Store it in a local **MySQL database**
    - Run SQL queries for data insights
    """)
    st.image("/Users/Pooja/Downloads/ChatGPT Image Oct 12, 2025, 10_35_07 PM.png", width=500)
    st.info("Use the sidebar to navigate between sections →")

# ---------- 2️⃣ FETCH DATA ----------
elif page.startswith("2️⃣"):
    st.header("🌐 Fetching Data")
    classifications = get_classifications()
    classification = st.selectbox("🎨 Choose a classification", classifications)
    st.session_state["classification"] = classification

    if st.button("📤 Fetch Data"):
        recs = fetch_artifacts(classification)
        if recs:
            st.session_state["data"] = recs
            st.success(f"✅ Fetched {len(recs)} records for '{classification}'")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("📋 Metadata Sample")
                st.json([{k:v for k,v in r.items() if k in ["id","title","culture"]} for r in recs[:50]])
            with col2:
                st.subheader("🖼️ Media Sample")
                st.json([{k:r.get(k) for k in ["id","imagecount","mediacount","colorcount"]} for r in recs[:50]])
            with col3:
                st.subheader("🌈 Colors Sample")
                color_data = []
                for r in recs[:50]:
                    if r.get("colors"):
                        color_data.extend(r["colors"])
                st.json(color_data[:50])

# ---------- 3️⃣ INSERT DATA ----------
elif page.startswith("3️⃣"):
    st.header("💾 Inserting Data into MySQL")
    if st.button("📥 Insert Data"):
        if "data" not in st.session_state:
            st.warning("⚠️ Please fetch data first from the 'Fetch Data' section.")
        else:
            insert_into_mysql(st.session_state["data"], st.session_state["classification"])
            st.balloons()

# ---------- 4️⃣ QUERY EXPLORER ----------
elif page.startswith("4️⃣"):
    st.header("🔍 Query Explorer")
    queries = {
    "① Artifacts from 11th Century Byzantine Culture":
        "SELECT * FROM artifact_metadata WHERE century='11th century' AND culture='Byzantine';",

    "② Unique Cultures in Artifacts":
        "SELECT DISTINCT culture FROM artifact_metadata WHERE culture IS NOT NULL ORDER BY culture;",

    "③ Artifacts from Archaic Period":
        "SELECT * FROM artifact_metadata WHERE period='Archaic Period';",

    "④ Artifact Titles by Accession Year (Desc)":
        "SELECT title, accessionyear FROM artifact_metadata WHERE accessionyear IS NOT NULL ORDER BY accessionyear DESC;",

    "⑤ Artifacts per Department":
        "SELECT department, COUNT(*) AS total FROM artifact_metadata GROUP BY department ORDER BY total DESC;",

    "⑥ Artifacts with More Than 1 Image":
        "SELECT * FROM artifact_media WHERE imagecount > 1;",

    "⑦ Average Rank of All Artifacts":
        "SELECT AVG(`rank`) AS avg_rank FROM artifact_media;",

    "⑧ Artifacts with Higher Colorcount than Mediaccount":
        "SELECT * FROM artifact_media WHERE colorcount > mediacount;",

    "⑨ Artifacts Created Between 1500 and 1600":
        "SELECT * FROM artifact_media WHERE datebegin >= 1500 AND dateend <= 1600;",

    "⑩ Artifacts with No Media Files":
        "SELECT * FROM artifact_media WHERE mediacount = 0 OR mediacount IS NULL;",

    "⑪ All Distinct Hues":
        "SELECT DISTINCT hue FROM artifact_colors WHERE hue IS NOT NULL ORDER BY hue;",

    "⑫ Top 5 Most Used Colors":
        "SELECT color, COUNT(*) AS frequency FROM artifact_colors GROUP BY color ORDER BY frequency DESC LIMIT 5;",

    "⑬ Average Coverage Percentage per Hue":
        "SELECT hue, ROUND(AVG(percent), 2) AS avg_percent FROM artifact_colors WHERE percent IS NOT NULL GROUP BY hue ORDER BY avg_percent DESC;",

    "⑭ Colors Used for Given Artifact ID":
        "SELECT * FROM artifact_colors WHERE objectid = {artifact_id};",

    "⑮ Total Number of Color Entries":
        "SELECT COUNT(*) AS total_colors FROM artifact_colors;",

    "⑯ Artifact Titles and Hues (Byzantine Culture)":
        """
        SELECT m.title, c.hue
        FROM artifact_metadata m
        JOIN artifact_colors c ON m.id = c.objectid
        WHERE LOWER(m.culture) LIKE '%%byzantine%%';
        """,

    "⑰ Artifact Titles with Associated Hues":
        """
        SELECT m.title, c.hue
        FROM artifact_metadata m
        JOIN artifact_colors c ON m.id = c.objectid
        ORDER BY m.title;
        """,

    "⑱ Artifacts with Period, Culture, and Media Rank":
        """
        SELECT m.title, m.culture, m.period, me.`rank`
        FROM artifact_metadata m
        JOIN artifact_media me ON m.id = me.objectid
        WHERE m.period IS NOT NULL;
        """,

    "⑲ Top 10 Artifacts with Hue 'Grey'":
        """
        SELECT m.title, c.hue, me.`rank`
        FROM artifact_metadata m
        JOIN artifact_colors c ON m.id = c.objectid
        JOIN artifact_media me ON m.id = me.objectid
        WHERE LOWER(c.hue) = 'grey'
        ORDER BY me.`rank` DESC
        LIMIT 10;
        """,

    "⑳ Artifacts per Classification (Avg Media Count)":
        """
        SELECT m.classification,
               COUNT(*) AS total_artifacts,
               ROUND(AVG(me.mediacount), 2) AS avg_media_count
        FROM artifact_metadata m
        JOIN artifact_media me ON m.id = me.objectid
        GROUP BY m.classification
        ORDER BY total_artifacts DESC;
        """,

    "㉑ Top 5 Cultures with the Most Artifacts":
        """
        SELECT culture, COUNT(*) AS total_artifacts
        FROM artifact_metadata
        WHERE culture IS NOT NULL
        GROUP BY culture
        ORDER BY total_artifacts DESC
        LIMIT 5;
        """,

    "㉒ Department with the Highest Average Accession Year":
        """
        SELECT department, ROUND(AVG(accessionyear), 2) AS avg_accession_year
        FROM artifact_metadata
        WHERE accessionyear IS NOT NULL
        GROUP BY department
        ORDER BY avg_accession_year DESC
        LIMIT 1;
        """,

    "㉓ Artifacts Made of Bronze":
        """
        SELECT id, title, medium, culture
        FROM artifact_metadata
        WHERE LOWER(medium) LIKE '%bronze%';
        """,

    "㉔ Compare Average Color Coverage (Red vs Blue)":
        """
        SELECT hue, ROUND(AVG(percent), 2) AS avg_coverage
        FROM artifact_colors
        WHERE LOWER(hue) IN ('red', 'blue')
        GROUP BY hue;
        """,

    "㉕ Century with the Most Artifacts":
        """
        SELECT century, COUNT(*) AS artifact_count
        FROM artifact_metadata
        WHERE century IS NOT NULL
        GROUP BY century
        ORDER BY artifact_count DESC
        LIMIT 1;
        """,

    "㉖ Top 5 Classifications with Most Diverse Cultures":
        """
        SELECT classification, COUNT(DISTINCT culture) AS unique_cultures
        FROM artifact_metadata
        WHERE culture IS NOT NULL
        GROUP BY classification
        ORDER BY unique_cultures DESC
        LIMIT 5;
        """,

    "㉗ Year Range (Min–Max) per Classification":
        """
        SELECT m.classification,
               MIN(me.datebegin) AS earliest_year,
               MAX(me.dateend) AS latest_year
        FROM artifact_metadata m
        JOIN artifact_media me ON m.id = me.objectid
        GROUP BY m.classification
        ORDER BY earliest_year;
        """,

    "㉘ Artifacts with High Image and Color Diversity":
        """
        SELECT m.title, me.imagecount, me.colorcount
        FROM artifact_metadata m
        JOIN artifact_media me ON m.id = me.objectid
        WHERE me.imagecount > 5 AND me.colorcount > 5
        ORDER BY me.imagecount DESC, me.colorcount DESC;
        """,

    "㉙ Percentage of Artifacts with Color Data":
        """
        SELECT 
            ROUND(
                (COUNT(DISTINCT c.objectid) / COUNT(DISTINCT m.id)) * 100, 2
            ) AS percent_with_color_data
        FROM artifact_metadata m
        LEFT JOIN artifact_colors c ON m.id = c.objectid;
        """,

    "㉚ Cultures with Highest Average Media Rank":
        """
        SELECT m.culture, ROUND(AVG(me.`rank`), 2) AS avg_rank
        FROM artifact_metadata m
        JOIN artifact_media me ON m.id = me.objectid
        WHERE m.culture IS NOT NULL
        GROUP BY m.culture
        ORDER BY avg_rank DESC
        LIMIT 5;
        """
    }


    selected_query = st.selectbox("🧠 Choose a Query", list(queries.keys()))
    if st.button("▶️ Run Query"):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(queries[selected_query])
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        st.dataframe([dict(zip(cols, r)) for r in rows], use_container_width=True)

# ---------- 5️⃣ CREATOR INFO ----------
elif page.startswith("5️⃣"):
    st.header("👩‍💻 Creator Info")
    st.markdown("""
    **Developed by:** Pooja Reddy Nedhunuri  
    

    🔗 [LinkedIn](https://www.linkedin.com/in/pooja-reddy-nedhunuri/) | [GitHub](https://github.com/pooja211reddy)
    """)
    
    st.markdown("""
<div style="text-align:center; font-size:16px;">
    🔍 Built with ⚡ <b>Streamlit</b> • 🗄️ <b>MySQL</b> • 🎨 <b>Harvard Art Museums API</b><br>
    💡 Delivering data-driven insights with precision.
</div>
""", unsafe_allow_html=True)