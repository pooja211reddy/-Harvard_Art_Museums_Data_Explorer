# 🏛️ Harvard Art Museums Data Explorer 🎨  

An interactive **Streamlit + MySQL** application that fetches, stores, and visualizes data from the **Harvard Art Museums API**.  
It enables users to dynamically query thousands of art artifact records and explore metadata, media details, and color patterns across cultures and periods.  

---

## 🚀 Features

- **🔹 ETL Pipeline:** Fetches and stores artifact data from the Harvard Art Museums API into MySQL.  
- **🔹 Streamlit Dashboard:** Enables real-time filtering, querying, and visualizations.  
- **🔹 Predefined SQL Queries:** Quickly explore insights on culture, media, color, and classification.  
- **🔹 Custom SQL Runner:** Execute your own queries for deeper exploration.  
- **🔹 Data Visualization:** View results in interactive tables and charts.  

---

## Workflow Overview

1️⃣ **Data Fetching:**  
   → Uses Harvard API to extract artifact details by classification (Paintings, Coins, Jewelry, etc.).  

2️⃣ **Data Storage:**  
   → Saves data into MySQL tables:
   - `artifact_metadata`
   - `artifact_media`
   - `artifact_colors`

3️⃣ **Data Exploration:**  
   → Query through Streamlit interface (predefined + custom SQL queries).  

4️⃣ **Visualization:**  
   → Display metadata, color palettes, and artifact metrics interactively.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/pooja211reddy/Harvard-Art-Museums-Data-Explorer.git
cd Harvard-Art-Museums-Data-Explorer
2️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
3️⃣ Configure MySQL
Create a database named harvard_art and run the script below (found in sql/create_tables.sql).

4️⃣ Run the Streamlit App
bash
Copy code
streamlit run harvard_artifacts.py
💾 Database Schema
Tables:

artifact_metadata

artifact_media

artifact_colors

Each table stores unique aspects of artifacts like title, medium, image count, hue, etc.

🧩 API Reference
Base API: Harvard Art Museums API

Example Endpoint:

arduino
Copy code
https://api.harvardartmuseums.org/object?apikey=YOUR_API_KEY
🖼️ Flow Diagram

🧑‍🎨 Credits
Developed by: Pooja Reddy Nedunuri
Powered by: Harvard Art Museums API • Streamlit • MySQL
