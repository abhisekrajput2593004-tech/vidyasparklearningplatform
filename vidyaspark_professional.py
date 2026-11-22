import os
import time
import urllib.parse
import pandas as pd
import streamlit as st

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ==========================================
# 1. PAGE CONFIG & BASIC MINIMAL THEME
# ==========================================
st.set_page_config(
    page_title="VidyaSpark | AI Study Companion",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Professional, restrained neutral theme */
    :root {
        --page: #f7f8fa;
        --surface: #ffffff;
        --surface-soft: #f1f3f5;
        --text: #20242a;
        --muted: #68717c;
        --border: #dfe3e8;
        --button: #252a31;
        --button-hover: #3b424b;
    }
    .stApp, [data-testid="stAppViewContainer"] { background: var(--page) !important; color: var(--text) !important; }
    .block-container { max-width: 1240px; padding: 2rem 2.2rem !important; }
    [data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
    h1, h2, h3, h4, h5, h6, p, label, li { color: var(--text) !important; }
    h1 { font-weight: 650 !important; letter-spacing: -0.025em; }
    h2, h3 { font-weight: 600 !important; }

    .bw-banner, .bw-metric, .sidebar-brand {
        background: var(--surface) !important; color: var(--text) !important;
        border: 1px solid var(--border) !important; border-radius: 10px !important;
        box-shadow: none !important; padding: 18px 20px !important; margin-bottom: 14px !important;
    }
    /* Resource cards: black background with white text */
    .bw-card {
        background: #000000 !important; color: #ffffff !important;
        border: 1px solid #333333 !important; border-radius: 8px !important;
        box-shadow: none !important; padding: 18px 20px !important; margin-bottom: 14px !important;
    }
    .bw-card h1, .bw-card h2, .bw-card h3, .bw-card h4, .bw-card h5, .bw-card h6,
    .bw-card p, .bw-card span, .bw-card b, .bw-card strong, .bw-card li {
        color: #ffffff !important;
    }
    .bw-banner { padding: 24px 26px !important; }
    .bw-banner h1, .bw-metric h2, .sidebar-brand h2 { color: var(--text) !important; }
    .bw-banner p, .bw-metric p, .sidebar-brand p { color: var(--muted) !important; }
    /* Only the four dashboard summary boxes: black background, white text */
    .bw-metric {
        background: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #222222 !important;
        text-align: center !important;
        border-radius: 10px !important;
        height: 138px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .bw-metric h2, .bw-metric p {
        color: #ffffff !important;
    }
    .bw-metric h2 { font-size: 1.8rem !important; font-weight: 650 !important; }
    .bw-card h4 { font-weight: 600 !important; }
    /* Dashboard important-topic cards: white surface with readable dark text */
    .bw-topic-card {
        background: #ffffff !important;
        color: #20242a !important;
        border: 1px solid #dfe3e8 !important;
    }
    .bw-topic-card h1, .bw-topic-card h2, .bw-topic-card h3,
    .bw-topic-card h4, .bw-topic-card h5, .bw-topic-card h6,
    .bw-topic-card p, .bw-topic-card span, .bw-topic-card b,
    .bw-topic-card strong, .bw-topic-card li {
        color: #20242a !important;
    }

    .stButton > button, .stLinkButton > a, button[kind],
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
        background: #ffffff !important; color: #20242a !important;
        border: 1px solid #cfd4da !important; border-radius: 7px !important;
        box-shadow: none !important; text-decoration: none !important; font-weight: 500 !important;
        transition: background 0.15s ease-in-out;
    }
    .stButton > button:hover, .stLinkButton > a:hover {
        background: #f1f3f5 !important; color: #20242a !important; border-color: #aeb5bd !important;
    }
    input, textarea, select, [data-baseweb="select"] {
        background: var(--surface) !important; color: var(--text) !important;
        border: 1px solid var(--border) !important; border-radius: 7px !important;
    }
    [data-testid="stMetric"] { background: var(--surface) !important; border: 1px solid var(--border) !important; box-shadow: none !important; border-radius: 10px !important; }
    [data-testid="stProgressBar"] > div > div { background: #555e69 !important; }
    hr { border-color: var(--border) !important; }
    a { color: #333b46 !important; }
    @media (max-width: 768px) { .block-container { padding: 1rem !important; } .bw-banner, .bw-card, .bw-metric { padding: 14px !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. HIDDEN GEMINI API KEY (FROM SECRETS)
# ==========================================
def get_hidden_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")

def ask_gemini(prompt, stream, language="English"):
    api_key = get_hidden_api_key()
    if not api_key:
        return "AI is not configured yet. Add GEMINI_API_KEY to Streamlit Secrets or your environment variables."
    if not GENAI_AVAILABLE:
        return "The Google GenAI package is not installed. Install project dependencies with: pip install -r requirements_final.txt"

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20000),
        )
        system_instruction = (
            f"You are VidyaSpark AI Tutor for students. Student Stream/Exam: {stream}. "
            f"Reply clearly in {language}. Use simple language, useful headings, and step-by-step explanations."
        )
        last_error = None
        # Retry transient gateway/rate-limit failures and switch models if one is busy.
        transient_statuses = {408, 429, 500, 502, 503, 504}
        model_names = ("gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash")
        for model_index, model_name in enumerate(model_names):
            attempts = 2 if model_index == 0 else 1
            for attempt in range(attempts):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(system_instruction=system_instruction),
                    )
                    if response and response.text:
                        return response.text
                    break
                except Exception as model_error:
                    last_error = model_error
                    model_status = getattr(model_error, "code", None) or getattr(model_error, "status_code", None)
                    is_timeout = type(model_error).__name__ == "APITimeoutError"
                    if model_status not in transient_statuses and model_status != 404 and not is_timeout:
                        break
                    if model_status in transient_statuses and attempt < attempts - 1:
                        time.sleep(0.7)
            if last_error is not None:
                model_status = getattr(last_error, "code", None) or getattr(last_error, "status_code", None)
                is_timeout = type(last_error).__name__ == "APITimeoutError"
                if model_status not in transient_statuses and model_status != 404 and not is_timeout:
                    break

        if last_error is None:
            return "Gemini returned an empty response. Please try again."
        exc = last_error
        status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if status in (401, 403):
            return "Gemini rejected the API key. Check that this key is enabled for the Gemini API."
        if status == 429:
            return "Gemini is rate-limiting requests or the API quota is reached. Wait a little and try again."
        if status == 404:
            return "None of the configured Gemini models is available for this API key. Check model access and try again."
        if status in transient_statuses or type(exc).__name__ == "APITimeoutError":
            return "Gemini is temporarily unavailable. The app retried with alternate models; please try again shortly."
        if status:
            return f"Gemini request failed (status {status}). Check the API configuration, then try again."
        return f"Gemini request failed ({type(exc).__name__}). Check your connection and try again."
    except Exception as exc:
        status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if status in (408, 500, 502, 503, 504) or type(exc).__name__ == "APITimeoutError":
            return "Gemini is temporarily unavailable. Please try again shortly."
        if status == 429:
            return "Gemini is rate-limiting requests or the API quota is reached. Wait a little and try again."
        if status in (401, 403):
            return "Gemini rejected the API key. Check that this key is enabled for the Gemini API."
        if status:
            return f"Gemini request failed (status {status}). Check the API configuration, then try again."
        return f"Gemini request failed ({type(exc).__name__}). Check your connection and try again."

def yt_search_url(query):
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

def yt_channel_search_url(channel):
    return yt_search_url(f"{channel} official YouTube channel")

# ==========================================
# 3. INITIAL DATA & SESSION STATE
# ==========================================
STREAMS = [
    "B.Tech CSE", "Mechanical", "Electrical", "Class 10/12 Boards",
    "JEE", "NEET", "UPSC", "SSC", "Banking/Railway", "SSB"
]

DEFAULT_RESOURCES = [
    {"Topic": "Python Programming Full Course", "Stream": "B.Tech CSE", "Channel": "CodeWithHarry (Hindi)", "Important": True, "URL": yt_search_url("Python Programming CodeWithHarry Hindi")},
    {"Topic": "DSA (Data Structures & Algorithms)", "Stream": "B.Tech CSE", "Channel": "Striver / Apna College", "Important": True, "URL": yt_search_url("DSA full course Apna College Striver")},
    {"Topic": "OS, DBMS & Computer Networks", "Stream": "B.Tech CSE", "Channel": "Gate Smashers", "Important": True, "URL": yt_search_url("OS DBMS CN Gate Smashers")},
    {"Topic": "C Programming One Shot", "Stream": "B.Tech CSE", "Channel": "College Wallah", "Important": True, "URL": yt_search_url("C Programming One Shot College Wallah")},
    {"Topic": "Thermodynamics & Fluid Mechanics", "Stream": "Mechanical", "Channel": "Gate Wallah", "Important": True, "URL": yt_search_url("Thermodynamics Fluid Mechanics Gate Wallah")},
    {"Topic": "Basic Electrical Engineering (BEE)", "Stream": "Electrical", "Channel": "Engineers Ki Pathshala", "Important": True, "URL": yt_search_url("Basic Electrical Engineering full course Hindi")},
    {"Topic": "Class 12 Physics & Maths One Shot", "Stream": "Class 10/12 Boards", "Channel": "Physics Wallah", "Important": True, "URL": yt_search_url("Class 12 Physics Maths One Shot Physics Wallah")},
    {"Topic": "JEE Physics Mechanics & Calculus", "Stream": "JEE", "Channel": "Physics Wallah / Mohit Tyagi", "Important": True, "URL": yt_search_url("JEE Physics Mechanics Calculus One Shot")},
    {"Topic": "NEET Biology NCERT Line by Line", "Stream": "NEET", "Channel": "Tarun Sir / PW", "Important": True, "URL": yt_search_url("NEET Biology NCERT line by line")},
    {"Topic": "UPSC Polity (Laxmikanth) & History", "Stream": "UPSC", "Channel": "StudyIQ IAS", "Important": True, "URL": yt_search_url("UPSC Laxmikanth Polity StudyIQ")},
    {"Topic": "SSC CGL Maths & Reasoning", "Stream": "SSC", "Channel": "Aditya Ranjan / Gagan Pratap", "Important": True, "URL": yt_search_url("SSC CGL Maths Reasoning Aditya Ranjan")},
    {"Topic": "RRB NTPC & Banking Quant + GA", "Stream": "Banking/Railway", "Channel": "Adda247 / Quick Tricks by Sahil Sir", "Important": True, "URL": yt_search_url("RRB NTPC Banking Quant Sahil Sir")},
    {"Topic": "SSB Interview OIR, PPDT & Psych Tests", "Stream": "SSB", "Channel": "Defence Wallah / SSB Crack", "Important": True, "URL": yt_search_url("SSB Interview complete preparation Hindi")},
]

def mcq(question, correct, wrong1, wrong2, wrong3):
    return (question, [correct, wrong1, wrong2, wrong3], correct)


# 30-question pools produce five overlapping but distinct 15-question papers
# for every stream. Correct answers are rotated through the option positions.
MOCK_QUESTION_BANKS = {
    "B.Tech CSE": [
        mcq("Which Python collection is mutable?", "List", "Tuple", "String", "Integer"),
        mcq("Which type is commonly used for key-value data in Python?", "Dictionary", "Tuple", "Set", "Boolean"),
        mcq("What does // do in Python?", "Floor division", "Exponentiation", "Modulo", "String join"),
        mcq("What is len('Vidya')?", "5", "4", "6", "7"),
        mcq("Which keyword defines a Python function?", "def", "func", "define", "method"),
        mcq("Which block handles an exception in Python?", "except", "catch", "error", "rescue"),
        mcq("Which Python collection is immutable?", "Tuple", "List", "Dictionary", "Set"),
        mcq("What does a Python set remove automatically?", "Duplicate values", "All strings", "Negative numbers", "Dictionary keys"),
        mcq("What values does range(5) produce?", "0 through 4", "1 through 5", "0 through 5", "1 through 4"),
        mcq("Which Python method initializes a new object?", "__init__", "__start__", "__newclass__", "__main__"),
        mcq("What does a C pointer store?", "Memory address", "Loop count", "Character only", "File name"),
        mcq("How does a C string end?", "Null character", "Newline only", "Comma", "Space"),
        mcq("What is the first index of a C array?", "0", "1", "-1", "Depends on length"),
        mcq("Which C function allocates memory dynamically?", "malloc", "printf", "scanf", "strlen"),
        mcq("Which C function prints formatted output?", "printf", "scanf", "malloc", "fopen"),
        mcq("Binary search requires what kind of input?", "Sorted data", "Random data only", "A linked list only", "Duplicate-free data"),
        mcq("Which structure follows LIFO order?", "Stack", "Queue", "Graph", "Heap file"),
        mcq("Which structure follows FIFO order?", "Queue", "Stack", "Tree", "Hash table"),
        mcq("Which structure is commonly used by BFS?", "Queue", "Stack", "Priority queue", "Array only"),
        mcq("Which structure is commonly used by DFS?", "Stack", "Queue", "Circular buffer", "Hash map"),
        mcq("What is the average lookup time in a hash table?", "O(1)", "O(n)", "O(log n)", "O(n log n)"),
        mcq("What is merge sort's usual time complexity?", "O(n log n)", "O(n^2)", "O(log n)", "O(1)"),
        mcq("What is a process in an operating system?", "A program in execution", "A stored file only", "A network cable", "A database table"),
        mcq("Which condition is needed for deadlock?", "Circular wait", "Fast CPU", "Large disk", "Open-source code"),
        mcq("What does virtual memory provide?", "An extended address space", "A faster keyboard", "A second CPU", "A database backup"),
        mcq("What must a primary key be?", "Unique for each row", "Repeated in every row", "Always a sentence", "Always a date"),
        mcq("Which SQL command retrieves rows?", "SELECT", "DELETE", "DROP", "ALTER"),
        mcq("What is a main goal of database normalization?", "Reduce data redundancy", "Increase duplicate data", "Encrypt every column", "Remove all keys"),
        mcq("Which transport protocol provides reliable delivery?", "TCP", "UDP", "ARP", "ICMP"),
        mcq("What does DNS translate?", "Domain names to IP addresses", "Pixels to colors", "Files to folders", "Ports to passwords"),
    ],
    "Mechanical": [
        mcq("What is the SI unit of force?", "Newton", "Joule", "Watt", "Pascal"),
        mcq("What is the SI unit of pressure?", "Pascal", "Newton", "Watt", "Kelvin"),
        mcq("Which law relates pressure and volume at constant temperature?", "Boyle's law", "Ohm's law", "Hooke's law", "Faraday's law"),
        mcq("What is the efficiency of a Carnot engine based on?", "Hot and cold reservoir temperatures", "Fuel color", "Engine mass only", "Cylinder count only"),
        mcq("Which process occurs at constant pressure?", "Isobaric", "Isochoric", "Isothermal", "Adiabatic"),
        mcq("Which process occurs at constant volume?", "Isochoric", "Isobaric", "Isothermal", "Polytropic only"),
        mcq("What is the SI unit of specific heat capacity?", "J/(kg·K)", "N/m", "W/m²", "Pa·s"),
        mcq("What does the first law of thermodynamics express?", "Conservation of energy", "Conservation of charge", "Conservation of momentum only", "Conservation of volume"),
        mcq("What is the SI unit of dynamic viscosity?", "Pa·s", "m/s", "kg/m³", "J/kg"),
        mcq("For incompressible steady flow, continuity represents conservation of what?", "Mass", "Temperature", "Viscosity", "Pressure only"),
        mcq("What is the Reynolds number used to estimate?", "Flow regime", "Surface color", "Heat capacity", "Gear ratio"),
        mcq("Which flow is typically orderly in layers?", "Laminar flow", "Turbulent flow", "Choked flow", "Cavitating flow"),
        mcq("What does a pump add to a fluid?", "Mechanical energy", "Electrical resistance", "Chemical composition", "Entropy only"),
        mcq("What is the SI unit of power?", "Watt", "Joule", "Newton", "Pascal"),
        mcq("What does a flywheel primarily store?", "Rotational kinetic energy", "Electrical charge", "Pressure energy only", "Chemical fuel"),
        mcq("Which law describes elastic deformation within a limit?", "Hooke's law", "Boyle's law", "Pascal's law", "Charles's law"),
        mcq("What is the neutral axis in a bent beam?", "A layer with zero longitudinal strain", "The topmost layer", "The point of maximum shear", "The beam's center of mass always"),
        mcq("What does Young's modulus relate?", "Stress to strain", "Force to power", "Pressure to volume", "Torque to speed"),
        mcq("Which test measures a material's resistance to indentation?", "Hardness test", "Creep test", "Fatigue test", "Impact test only"),
        mcq("What is fatigue failure caused by?", "Repeated cyclic loading", "One static measurement", "Uniform heating only", "Low density"),
        mcq("Which manufacturing process forces material through a die?", "Extrusion", "Casting", "Drilling", "Grinding"),
        mcq("Which process joins metal by melting a filler or base material?", "Welding", "Turning", "Milling", "Knurling"),
        mcq("Which machine tool commonly produces a cylindrical surface?", "Lathe", "Shaper", "Planer", "Broach"),
        mcq("What does a milling cutter use to remove material?", "Rotating multi-point teeth", "A stationary single-point tool only", "A chemical bath", "A laser mirror"),
        mcq("What is the purpose of a bearing?", "Support motion and reduce friction", "Increase leakage", "Store fuel", "Measure voltage"),
        mcq("What does a gear train transmit?", "Rotary motion and torque", "Heat only", "Fluid pressure only", "Light"),
        mcq("What is the SI unit of torque?", "N·m", "N/m²", "kg/m³", "J/s²"),
        mcq("What does a safety factor compare?", "Strength to design load or stress", "Speed to temperature", "Mass to volume", "Cost to color"),
        mcq("Which heat transfer mode needs no material medium?", "Radiation", "Conduction", "Convection", "Diffusion"),
        mcq("What is cavitation in a pump?", "Vapor bubbles forming and collapsing", "A gear tooth slipping", "A shaft expanding evenly", "A bearing being lubricated"),
    ],
    "Electrical": [
        mcq("What is the SI unit of electric current?", "Ampere", "Volt", "Ohm", "Watt"),
        mcq("What is the SI unit of resistance?", "Ohm", "Ampere", "Coulomb", "Tesla"),
        mcq("Which law states V = IR?", "Ohm's law", "Kirchhoff's current law", "Faraday's law", "Lenz's law"),
        mcq("In a series circuit, which quantity is the same through each component?", "Current", "Voltage", "Resistance", "Power"),
        mcq("In a parallel circuit, which quantity is shared across branches?", "Voltage", "Current", "Charge per second", "Resistance"),
        mcq("What is the SI unit of capacitance?", "Farad", "Henry", "Weber", "Siemens"),
        mcq("What is the SI unit of inductance?", "Henry", "Farad", "Tesla", "Coulomb"),
        mcq("What does a capacitor store?", "Electric charge and field energy", "Mechanical torque", "Magnetic poles only", "Fuel"),
        mcq("What does an inductor oppose?", "Change in current", "Change in resistance only", "All voltage", "Electric charge at rest"),
        mcq("Which law describes induced EMF from changing magnetic flux?", "Faraday's law", "Ohm's law", "Coulomb's law", "Hooke's law"),
        mcq("What does Lenz's law determine?", "Direction of induced current", "Wire resistance value", "Battery capacity", "Motor speed rating"),
        mcq("Which device converts electrical energy to mechanical rotation?", "Electric motor", "Transformer", "Rectifier", "Fuse"),
        mcq("Which device changes AC voltage levels by induction?", "Transformer", "DC motor", "Battery", "Fuse"),
        mcq("A transformer normally operates with which supply?", "Alternating current", "Steady direct current", "Static charge", "Mechanical input only"),
        mcq("What is the frequency of DC?", "0 Hz", "50 Hz", "60 Hz", "100 Hz"),
        mcq("What is the SI unit of magnetic flux?", "Weber", "Tesla", "Henry", "Farad"),
        mcq("What is the SI unit of magnetic flux density?", "Tesla", "Weber", "Volt", "Ampere"),
        mcq("What does a diode primarily allow?", "Current mainly in one direction", "Equal current both ways", "Only mechanical motion", "No current under any condition"),
        mcq("What is a rectifier used for?", "Convert AC to DC", "Convert DC to AC only", "Increase resistance", "Store magnetic flux"),
        mcq("What is an inverter used for?", "Convert DC to AC", "Convert AC to DC", "Measure current", "Protect a circuit from overload only"),
        mcq("What does a fuse protect against?", "Excessive current", "Low light", "Low frequency only", "Reverse rotation"),
        mcq("What does Kirchhoff's current law express?", "Current conservation at a node", "Energy conservation in a cycle", "Magnetic flux conservation", "Power factor correction"),
        mcq("What does Kirchhoff's voltage law express?", "Voltage sum around a closed loop is zero", "Current is same in all branches", "Resistance is always zero", "Frequency is constant"),
        mcq("What is the power factor of a purely resistive AC load?", "1", "0", "-1", "0.5"),
        mcq("What is the synchronous speed of an AC motor related to?", "Supply frequency and pole count", "Wire color only", "Bearing size only", "Ambient light"),
        mcq("Which motor commonly uses a commutator?", "DC motor", "Squirrel-cage induction motor", "Synchronous motor", "Transformer"),
        mcq("What is earthing intended to provide?", "A low-resistance path for fault current", "A higher supply voltage", "Extra motor torque", "A source of AC"),
        mcq("What does an oscilloscope display?", "Electrical signals versus time", "Wire mass", "Insulation color", "Mechanical stress only"),
        mcq("What is the SI unit of electrical power?", "Watt", "Volt", "Ohm", "Ampere-hour"),
        mcq("What is a three-phase system commonly used for?", "Efficient power transmission and motors", "Storing static charge", "Replacing all DC circuits", "Measuring temperature"),
    ],
    "Class 10/12 Boards": [
        mcq("What is the value of sin 30°?", "1/2", "√3/2", "1", "0"),
        mcq("What is the value of cos 60°?", "1/2", "√3/2", "1", "0"),
        mcq("What is the derivative of x²?", "2x", "x", "x³", "2"),
        mcq("What is the slope of a horizontal line?", "0", "1", "Undefined", "-1"),
        mcq("What is the sum of angles in a triangle?", "180°", "90°", "270°", "360°"),
        mcq("What is the quadratic formula discriminant?", "b² − 4ac", "b² + 4ac", "a² − 4bc", "2a + b"),
        mcq("What is the SI unit of electric charge?", "Coulomb", "Ampere", "Volt", "Ohm"),
        mcq("Which lens converges parallel rays?", "Convex lens", "Concave lens", "Plane glass", "Prism only"),
        mcq("What is the SI unit of frequency?", "Hertz", "Newton", "Joule", "Pascal"),
        mcq("Which mirror is commonly used as a rear-view mirror?", "Convex mirror", "Concave mirror", "Plane mirror only", "Cylindrical mirror"),
        mcq("What is the chemical formula of water?", "H₂O", "CO₂", "O₂", "NaCl"),
        mcq("What is the pH of a neutral solution at room temperature?", "7", "0", "1", "14"),
        mcq("Which gas is released in photosynthesis?", "Oxygen", "Nitrogen", "Hydrogen", "Methane"),
        mcq("What is the chemical symbol for sodium?", "Na", "So", "S", "N"),
        mcq("Which particle has a negative charge?", "Electron", "Proton", "Neutron", "Nucleus"),
        mcq("What is the basic unit of heredity?", "Gene", "Tissue", "Organ", "Cell wall"),
        mcq("Which organelle is known as the cell's powerhouse?", "Mitochondrion", "Ribosome", "Golgi body", "Vacuole"),
        mcq("Which blood cells help fight infection?", "White blood cells", "Red blood cells", "Platelets", "Plasma only"),
        mcq("Which part of a plant absorbs most water?", "Root hairs", "Petals", "Fruit", "Pollen"),
        mcq("What is the main function of the human alveoli?", "Gas exchange", "Pump blood", "Digest proteins", "Filter urine"),
        mcq("Who wrote India's national anthem?", "Rabindranath Tagore", "Bankim Chandra Chatterjee", "Sarojini Naidu", "Subhas Chandra Bose"),
        mcq("What is the past tense of 'go'?", "Went", "Goed", "Gone", "Going"),
        mcq("Which word is a synonym of 'rapid'?", "Swift", "Dull", "Quiet", "Late"),
        mcq("Which punctuation ends a direct question?", "Question mark", "Comma", "Colon", "Semicolon"),
        mcq("What is the main idea of a paragraph called?", "Central idea", "Footnote", "Caption", "Appendix"),
        mcq("What is the capital of India?", "New Delhi", "Mumbai", "Kolkata", "Chennai"),
        mcq("Which is the largest planet in the Solar System?", "Jupiter", "Earth", "Mars", "Venus"),
        mcq("What is Earth's natural satellite?", "The Moon", "Mars", "The Sun", "Europa"),
        mcq("Which gas is most abundant in Earth's atmosphere?", "Nitrogen", "Oxygen", "Carbon dioxide", "Argon"),
        mcq("What is the process of liquid water becoming vapor?", "Evaporation", "Condensation", "Freezing", "Sublimation"),
    ],
    "JEE": [
        mcq("What is the SI unit of momentum?", "kg·m/s", "N/m", "J/s", "kg/m³"),
        mcq("What is the acceleration due to gravity near Earth's surface approximately?", "9.8 m/s²", "3.0 m/s²", "6.7 m/s²", "15 m/s²"),
        mcq("What is the work done by a perpendicular force over displacement?", "0", "Fd", "F/d", "Infinite"),
        mcq("What is the SI unit of electric field?", "N/C", "C/N", "J/s", "A·s"),
        mcq("What is the charge of an electron?", "−1.602 × 10⁻¹⁹ C", "+1.602 × 10⁻¹⁹ C", "0 C", "−1 C"),
        mcq("What is the value of Avogadro's constant approximately?", "6.022 × 10²³ mol⁻¹", "3.00 × 10⁸ mol⁻¹", "9.81 mol⁻¹", "1.60 × 10⁻¹⁹ mol⁻¹"),
        mcq("What is the pH of a neutral aqueous solution at 25°C?", "7", "1", "10", "14"),
        mcq("Which bond involves sharing electron pairs?", "Covalent bond", "Ionic bond", "Metallic bond only", "Hydrogen bond only"),
        mcq("What is the hybridization of carbon in methane?", "sp³", "sp²", "sp", "dsp²"),
        mcq("Which gas law relates pressure and volume inversely at constant temperature?", "Boyle's law", "Charles's law", "Avogadro's law", "Graham's law"),
        mcq("What is the derivative of sin x?", "cos x", "−cos x", "tan x", "−sin x"),
        mcq("What is the integral of 1/x with respect to x?", "ln|x| + C", "x² + C", "eˣ + C", "1/x² + C"),
        mcq("What is the determinant of [[a,b],[c,d]]?", "ad − bc", "ab − cd", "ac − bd", "a + b + c + d"),
        mcq("What is the slope of a line perpendicular to slope m?", "−1/m", "m", "1/m", "−m"),
        mcq("What is the sum of the first n natural numbers?", "n(n+1)/2", "n²", "n(n−1)/2", "2n+1"),
        mcq("What is the SI unit of magnetic field?", "Tesla", "Weber", "Henry", "Farad"),
        mcq("What is the escape speed from a planet of mass M and radius R?", "√(2GM/R)", "GM/R", "√(GM/R²)", "2GM/R²"),
        mcq("For an ideal gas, which relation is the equation of state?", "PV = nRT", "P = nVRT", "PT = nRV", "PV = RT/n"),
        mcq("What is the oxidation number of oxygen in most compounds?", "−2", "+2", "−1 always", "0 always"),
        mcq("Which element has atomic number 1?", "Hydrogen", "Helium", "Lithium", "Carbon"),
        mcq("What is the conjugate acid of NH₃?", "NH₄⁺", "NH₂⁻", "NO₃⁻", "N₂H₄"),
        mcq("Which quantum number describes an orbital's shape?", "Azimuthal quantum number l", "Principal quantum number n", "Magnetic quantum number mₗ", "Spin quantum number mₛ"),
        mcq("What is the maximum number of electrons in a shell with principal number n?", "2n²", "n²", "2n", "n + 2"),
        mcq("What is the unit of rate constant for a first-order reaction?", "s⁻¹", "mol·L⁻¹·s⁻¹", "L·mol⁻¹·s⁻¹", "mol²·L⁻²"),
        mcq("Which law describes the relation between current and magnetic field direction?", "Ampère's circuital law", "Boyle's law", "Hooke's law", "Raoult's law"),
        mcq("What is the SI unit of capacitance?", "Farad", "Henry", "Weber", "Tesla"),
        mcq("What is the range of sin x?", "−1 to 1", "0 to infinity", "−infinity to infinity", "0 to 2π"),
        mcq("What is the probability of an impossible event?", "0", "1", "1/2", "Undefined"),
        mcq("What is the magnitude of the vector (3,4)?", "5", "7", "12", "1"),
        mcq("What is the SI unit of Planck's constant?", "J·s", "J/s", "N/m", "kg·m/s²"),
    ],
    "NEET": [
        mcq("What is the basic structural and functional unit of life?", "Cell", "Tissue", "Organ", "Molecule"),
        mcq("Which organelle carries out photosynthesis?", "Chloroplast", "Mitochondrion", "Ribosome", "Lysosome"),
        mcq("Which molecule carries genetic information in most organisms?", "DNA", "ATP", "Glucose", "Cellulose"),
        mcq("Where does glycolysis occur?", "Cytoplasm", "Nucleus", "Mitochondrial matrix", "Golgi apparatus"),
        mcq("Which blood cells transport most oxygen?", "Red blood cells", "White blood cells", "Platelets", "Lymphocytes only"),
        mcq("Which hormone lowers blood glucose?", "Insulin", "Glucagon", "Adrenaline", "Thyroxine"),
        mcq("Which part of a neuron receives most incoming signals?", "Dendrites", "Axon terminal", "Myelin sheath", "Node of Ranvier"),
        mcq("Which vessel carries oxygenated blood from lungs to heart?", "Pulmonary vein", "Pulmonary artery", "Vena cava", "Aorta"),
        mcq("Where does most nutrient absorption occur?", "Small intestine", "Stomach", "Large intestine", "Esophagus"),
        mcq("Which plant tissue transports water upward?", "Xylem", "Phloem", "Epidermis", "Cortex only"),
        mcq("What is the functional unit of the kidney?", "Nephron", "Neuron", "Alveolus", "Villus"),
        mcq("Which cells produce antibodies?", "Plasma cells", "Red blood cells", "Platelets", "Osteocytes"),
        mcq("What is the usual chromosome number in a human somatic cell?", "46", "23", "44", "48"),
        mcq("Which process produces gametes?", "Meiosis", "Mitosis", "Binary fission", "Budding"),
        mcq("Which molecule is the cell's main short-term energy currency?", "ATP", "DNA", "RNA", "Glycogen only"),
        mcq("What is the pH of neutral water at 25°C?", "7", "0", "5", "14"),
        mcq("Which bond links amino acids in a protein?", "Peptide bond", "Glycosidic bond", "Phosphodiester bond", "Hydrogen bond only"),
        mcq("Which vitamin is synthesized in skin after sunlight exposure?", "Vitamin D", "Vitamin C", "Vitamin B₁₂", "Vitamin K only"),
        mcq("Which gas is released during photosynthesis?", "Oxygen", "Carbon dioxide", "Nitrogen", "Ammonia"),
        mcq("What is the main site of aerobic respiration in eukaryotic cells?", "Mitochondrion", "Ribosome", "Lysosome", "Nucleolus"),
        mcq("What is the SI unit of force?", "Newton", "Joule", "Watt", "Pascal"),
        mcq("Which lens corrects myopia?", "Concave lens", "Convex lens", "Cylindrical only", "Plane glass"),
        mcq("What is the SI unit of electric current?", "Ampere", "Volt", "Ohm", "Coulomb"),
        mcq("What is the approximate acceleration due to gravity on Earth?", "9.8 m/s²", "1.6 m/s²", "3.7 m/s²", "24.8 m/s²"),
        mcq("What is the SI unit of frequency?", "Hertz", "Newton", "Joule", "Tesla"),
        mcq("What is the chemical symbol for potassium?", "K", "P", "Po", "Pt"),
        mcq("Which gas law states V is proportional to T at constant pressure?", "Charles's law", "Boyle's law", "Dalton's law", "Henry's law"),
        mcq("What is the oxidation state of sodium in NaCl?", "+1", "−1", "+2", "0"),
        mcq("Which macromolecule is made of nucleotide monomers?", "Nucleic acid", "Protein", "Lipid", "Polysaccharide"),
        mcq("Which ecological level includes organisms and their physical environment?", "Ecosystem", "Population", "Community", "Species"),
    ],
    "UPSC": [
        mcq("Who is the constitutional head of the Union of India?", "President", "Prime Minister", "Chief Justice", "Speaker"),
        mcq("Which body conducts elections to Parliament in India?", "Election Commission of India", "UPSC", "Finance Commission", "NITI Aayog"),
        mcq("Which part of the Constitution contains Fundamental Rights?", "Part III", "Part I", "Part IV", "Part V"),
        mcq("Directive Principles of State Policy are in which part?", "Part IV", "Part III", "Part II", "Part VI"),
        mcq("Who appoints the Prime Minister of India?", "President", "Chief Election Commissioner", "Lok Sabha Speaker", "Chief Justice"),
        mcq("What is the maximum strength of the Lok Sabha under the Constitution?", "552", "250", "500", "750"),
        mcq("Which house of Parliament is a permanent body?", "Rajya Sabha", "Lok Sabha", "Both dissolve together", "Neither"),
        mcq("Who presides over the Lok Sabha?", "Speaker", "President", "Vice-President", "Attorney General"),
        mcq("Which amendment lowered the voting age to 18?", "61st Amendment", "42nd Amendment", "44th Amendment", "73rd Amendment"),
        mcq("Which institution audits the accounts of the Union and states?", "Comptroller and Auditor General", "Election Commission", "Finance Ministry", "UPSC"),
        mcq("In which year did the Battle of Plassey take place?", "1757", "1764", "1857", "1942"),
        mcq("Who led the Dandi March in 1930?", "Mahatma Gandhi", "Jawaharlal Nehru", "Sardar Patel", "B. R. Ambedkar"),
        mcq("Who founded the Maurya Empire?", "Chandragupta Maurya", "Ashoka", "Harsha", "Samudragupta"),
        mcq("Which movement began with the 1942 resolution?", "Quit India Movement", "Non-Cooperation Movement", "Swadeshi Movement", "Khilafat Movement"),
        mcq("Who was the first Mughal emperor in India?", "Babur", "Akbar", "Humayun", "Shah Jahan"),
        mcq("Which latitude passes through the middle of India?", "Tropic of Cancer", "Equator", "Arctic Circle", "Tropic of Capricorn"),
        mcq("Which river is often called the Dakshin Ganga?", "Godavari", "Narmada", "Kaveri", "Mahanadi"),
        mcq("Which soil is especially suitable for cotton cultivation?", "Black soil", "Laterite soil", "Mountain soil", "Desert soil"),
        mcq("Which monsoon brings most rainfall to India?", "Southwest monsoon", "Northeast monsoon only", "Western disturbances", "Local sea breeze"),
        mcq("What is India's southernmost point?", "Indira Point", "Kanyakumari", "Rameswaram", "Minicoy"),
        mcq("Which body issues most currency notes in India?", "Reserve Bank of India", "SEBI", "State Bank of India", "NABARD"),
        mcq("What does GDP measure?", "Value of final goods and services produced domestically", "Government tax rate only", "Total exports only", "Population growth"),
        mcq("Which tax is generally levied on the supply of goods and services in India?", "GST", "Wealth tax", "Customs duty only", "Corporation tax only"),
        mcq("What is inflation?", "A sustained rise in the general price level", "A fall in population", "A rise in rainfall", "A decline in all wages"),
        mcq("Which organization publishes India's national income estimates?", "National Statistical Office", "Election Commission", "UPSC", "Supreme Court"),
        mcq("Which gas is a major anthropogenic greenhouse gas?", "Carbon dioxide", "Argon", "Helium", "Neon"),
        mcq("Which international agreement focuses on ozone-depleting substances?", "Montreal Protocol", "Kyoto Protocol", "Ramsar Convention", "Basel Convention"),
        mcq("What is biodiversity?", "Variety of life at different levels", "Only forest area", "Only crop yield", "A type of mineral"),
        mcq("Which Indian body advises on wildlife conservation?", "National Board for Wildlife", "Finance Commission", "UPSC", "Goods and Services Tax Council"),
        mcq("Where is the headquarters of the United Nations?", "New York City", "Geneva", "Paris", "Vienna"),
        mcq("Which court is the highest judicial authority in India?", "Supreme Court", "High Court", "District Court", "Lok Adalat"),
    ],
    "SSC": [
        mcq("What is 25% of 240?", "60", "40", "50", "80"),
        mcq("If 3x = 45, what is x?", "15", "12", "18", "20"),
        mcq("What is the average of 8, 10, and 12?", "10", "9", "11", "12"),
        mcq("A train covers 120 km in 2 hours. What is its speed?", "60 km/h", "40 km/h", "80 km/h", "100 km/h"),
        mcq("What is the simple interest on ₹1,000 at 10% for 2 years?", "₹200", "₹100", "₹150", "₹250"),
        mcq("What is the HCF of 18 and 24?", "6", "3", "12", "2"),
        mcq("What is the LCM of 6 and 8?", "24", "12", "48", "14"),
        mcq("A product costs ₹500 after a 20% discount. What was its marked price?", "₹625", "₹600", "₹650", "₹700"),
        mcq("What is 3/5 expressed as a percentage?", "60%", "30%", "50%", "65%"),
        mcq("What is the perimeter of a square of side 7 cm?", "28 cm", "14 cm", "49 cm", "21 cm"),
        mcq("Find the next number: 2, 4, 8, 16, __", "32", "24", "30", "64"),
        mcq("If CAT is coded as DBU, how is DOG coded by the same rule?", "EPH", "CNG", "FQI", "EOG"),
        mcq("Which direction is opposite to north-east?", "South-west", "North-west", "South-east", "East"),
        mcq("Choose the odd one out: 3, 5, 7, 9", "9", "3", "5", "7"),
        mcq("If today is Monday, what day will it be after 10 days?", "Thursday", "Wednesday", "Friday", "Saturday"),
        mcq("Which word is a synonym of 'brief'?", "Concise", "Lengthy", "Unclear", "Distant"),
        mcq("Choose the correct spelling.", "Accommodation", "Accomodation", "Acommodation", "Accommadation"),
        mcq("What is the plural of 'criterion'?", "Criteria", "Criterions only", "Criterias", "Criterion's"),
        mcq("Choose the antonym of 'ancient'.", "Modern", "Old", "Historic", "Former"),
        mcq("Which sentence is grammatically correct?", "She has finished her work.", "She have finished her work.", "She has finish her work.", "She finished has her work."),
        mcq("Who was the first President of India?", "Dr. Rajendra Prasad", "Dr. S. Radhakrishnan", "Zakir Husain", "V. V. Giri"),
        mcq("What is the capital of Rajasthan?", "Jaipur", "Jodhpur", "Udaipur", "Bikaner"),
        mcq("Which planet is known as the Red Planet?", "Mars", "Venus", "Jupiter", "Mercury"),
        mcq("Which is the largest ocean on Earth?", "Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "Arctic Ocean"),
        mcq("Which organ filters blood to form urine?", "Kidney", "Liver", "Lung", "Pancreas"),
        mcq("What is the SI unit of force?", "Newton", "Joule", "Watt", "Pascal"),
        mcq("Which vitamin is produced in skin by sunlight?", "Vitamin D", "Vitamin A", "Vitamin C", "Vitamin B₁"),
        mcq("Which metal is liquid at room temperature?", "Mercury", "Iron", "Aluminium", "Copper"),
        mcq("What is the chemical symbol for iron?", "Fe", "Ir", "In", "I"),
        mcq("Which constitutional body conducts elections in India?", "Election Commission of India", "UPSC", "CAG", "Finance Commission"),
    ],
    "Banking/Railway": [
        mcq("Which institution determines India's policy repo rate?", "Reserve Bank of India", "SEBI", "SBI", "NABARD"),
        mcq("Where is the headquarters of Indian Railways?", "New Delhi", "Mumbai", "Kolkata", "Chennai"),
        mcq("If 20% of x is 40, what is x?", "200", "100", "150", "250"),
        mcq("What is 15% of ₹800?", "₹120", "₹100", "₹140", "₹160"),
        mcq("Find the average of 12, 18, and 24.", "18", "16", "20", "22"),
        mcq("A train travels 180 km in 3 hours. What is its average speed?", "60 km/h", "45 km/h", "75 km/h", "90 km/h"),
        mcq("What is the simple interest on ₹2,000 at 5% for 3 years?", "₹300", "₹200", "₹250", "₹350"),
        mcq("If the ratio is 2:3 and the total is 50, what is the smaller share?", "20", "15", "25", "30"),
        mcq("What is the compound amount on ₹1,000 at 10% annually for one year?", "₹1,100", "₹1,010", "₹1,200", "₹1,090"),
        mcq("A person buys for ₹400 and sells for ₹500. What is the profit percentage?", "25%", "20%", "10%", "30%"),
        mcq("Which body regulates the securities market in India?", "SEBI", "RBI", "IRDAI", "NABARD"),
        mcq("Which institution is India's central bank?", "Reserve Bank of India", "State Bank of India", "Punjab National Bank", "Bank of Baroda"),
        mcq("What does ATM stand for?", "Automated Teller Machine", "Automatic Transfer Method", "Account Tracking Module", "Anytime Transaction Mode"),
        mcq("What is a cheque?", "An instruction to a bank to pay money", "A type of tax", "A railway ticket", "A loan agreement only"),
        mcq("What does KYC stand for in banking?", "Know Your Customer", "Keep Your Cash", "Key Yield Calculation", "Know Your Credit"),
        mcq("Which train component provides traction power to the wheels?", "Traction motor", "Pantograph only", "Brake shoe", "Coupler"),
        mcq("What does a railway signal primarily communicate?", "Movement authority or caution", "Passenger fare only", "Train interior temperature", "Track ownership"),
        mcq("Which gauge is 1,676 mm wide?", "Broad gauge", "Metre gauge", "Narrow gauge", "Standard gauge"),
        mcq("What is the main purpose of railway sleepers?", "Support rails and maintain gauge", "Power the locomotive", "Brake the train", "Carry overhead wires"),
        mcq("Which device changes electrical power into mechanical traction in an electric locomotive?", "Traction motor", "Transformer only", "Fuse", "Pantograph"),
        mcq("Find the next number: 5, 10, 20, 40, __", "80", "60", "70", "100"),
        mcq("Choose the odd one out: 2, 3, 5, 9", "9", "2", "3", "5"),
        mcq("If EAST is coded as FBTU, how is WEST coded?", "XFTU", "VDRS", "XFSU", "YFTU"),
        mcq("A is taller than B, and B is taller than C. Who is shortest?", "C", "A", "B", "Cannot be determined"),
        mcq("What is the angle between clock hands at 3:00?", "90°", "60°", "120°", "180°"),
        mcq("Which word is a synonym of 'assist'?", "Help", "Hinder", "Refuse", "Delay"),
        mcq("Choose the antonym of 'expand'.", "Contract", "Enlarge", "Extend", "Increase"),
        mcq("What is the plural of 'analysis'?", "Analyses", "Analysises", "Analysis", "Analysi"),
        mcq("Which is the largest planet in the Solar System?", "Jupiter", "Saturn", "Earth", "Neptune"),
        mcq("Who appoints the Governor of an Indian state?", "President of India", "Chief Minister", "State Assembly", "Chief Justice of India"),
    ],
    "SSB": [
        mcq("In the SSB process, what does OIR stand for?", "Officer Intelligence Rating", "Operational Interview Review", "Objective Intelligence Report", "Officer Interview Rank"),
        mcq("What is PPDT commonly expanded as?", "Picture Perception and Discussion Test", "Personal Performance and Decision Trial", "Picture Planning and Design Task", "Psychological Personality Development Test"),
        mcq("Which quality is most useful in a group discussion?", "Clear, respectful communication", "Interrupting others", "Ignoring the topic", "Speaking without listening"),
        mcq("What should a candidate do when they do not know an answer?", "Respond honestly and stay composed", "Invent a dramatic story", "Blame another candidate", "Refuse every question"),
        mcq("What does teamwork require?", "Cooperation toward a shared goal", "Competition within the team", "Avoiding communication", "One person doing every task"),
        mcq("Which action best demonstrates responsibility?", "Accepting accountability for a task", "Hiding a mistake", "Waiting for others to act", "Ignoring a deadline"),
        mcq("What is a practical first step in solving a group problem?", "Understand the situation and goal", "Argue before hearing facts", "Choose a solution randomly", "Leave the discussion"),
        mcq("Which is an example of initiative?", "Starting a useful task without needless delay", "Avoiding all decisions", "Waiting for repeated reminders", "Taking credit for others' work"),
        mcq("What should a leader do when a teammate makes a mistake?", "Address it calmly and help correct it", "Publicly insult them", "Hide all evidence", "Abandon the task"),
        mcq("What is an effective way to manage limited time?", "Prioritize tasks by urgency and importance", "Do easy tasks only", "Ignore the deadline", "Change the goal repeatedly"),
        mcq("Which response shows adaptability?", "Adjusting a plan when new facts arise", "Rejecting every new idea", "Repeating a failed plan", "Avoiding feedback"),
        mcq("What is active listening?", "Paying attention and checking understanding", "Planning a reply while ignoring the speaker", "Speaking over others", "Changing the subject"),
        mcq("In a situation test, what makes a response practical?", "A safe and feasible action", "A risky heroic gesture", "An impossible promise", "Doing nothing in every case"),
        mcq("What should a candidate do after receiving constructive feedback?", "Consider it and improve", "Dismiss it automatically", "Argue with the observer", "Blame the group"),
        mcq("Which behaviour supports sound judgment?", "Weighing facts and likely consequences", "Acting only on rumors", "Ignoring safety", "Choosing the loudest opinion"),
        mcq("What should come first in an emergency?", "Protect people and seek appropriate help", "Take photos", "Spread unverified news", "Leave others without warning"),
        mcq("What is the role of the Indian Armed Forces?", "Defend the country and support national security", "Set monetary policy", "Conduct school examinations", "Regulate the stock market"),
        mcq("Which service primarily protects India's maritime interests?", "Indian Navy", "Indian Air Force", "Indian Army only", "Border Roads Organisation"),
        mcq("Which service primarily operates military aircraft?", "Indian Air Force", "Indian Navy only", "Indian Army only", "Railway Protection Force"),
        mcq("What is the National Defence Academy known for?", "Joint pre-commission training of cadets", "Training bank officers", "Civilian railway recruitment", "Medical licensing"),
        mcq("What is the National War Memorial located in?", "New Delhi", "Mumbai", "Hyderabad", "Jaipur"),
        mcq("What does the Indian Army's motto 'Service Before Self' emphasize?", "Duty and service", "Personal fame", "Avoiding teamwork", "Financial profit"),
        mcq("Which quality helps maintain discipline in a team?", "Consistent respect for agreed standards", "Changing rules for convenience", "Ignoring instructions", "Avoiding accountability"),
        mcq("What should a speaker do to make a short briefing clear?", "State the key point and supporting facts", "Use unrelated stories", "Speak as quickly as possible", "Avoid a conclusion"),
        mcq("Which is the best way to disagree in a discussion?", "Explain reasons respectfully", "Attack the person", "Shout over the group", "Refuse to listen"),
        mcq("What is resilience?", "Recovering and continuing after setbacks", "Never making a plan", "Avoiding every challenge", "Refusing to learn"),
        mcq("Which action best reflects self-discipline?", "Following a useful routine consistently", "Working only when watched", "Ignoring preparation", "Changing goals every hour"),
        mcq("If a map scale is 1:50,000, what does 1 cm represent?", "500 m", "50 m", "5 km", "50 km"),
        mcq("Which direction is opposite to south-east?", "North-west", "North-east", "South-west", "West"),
        mcq("Find the next number: 3, 6, 12, 24, __", "48", "36", "42", "30"),
        mcq("What is a good way to prepare for a personal interview?", "Reflect honestly on experiences and goals", "Memorize invented achievements", "Avoid learning about oneself", "Prepare only one-word answers"),
    ],
}


def build_sample_papers():
    papers = []
    papers_per_stream = 5
    questions_per_paper = 15
    for stream_name, bank in MOCK_QUESTION_BANKS.items():
        for test_number in range(papers_per_stream):
            start = test_number * 5
            questions = []
            for question_number in range(questions_per_paper):
                question, options, answer = bank[(start + question_number) % len(bank)]
                option_shift = (test_number + question_number) % len(options)
                rotated_options = options[option_shift:] + options[:option_shift]
                questions.append((question, rotated_options, answer))
            papers.append({
                "Title": f"{stream_name} — Mock Test {test_number + 1}",
                "Stream": stream_name,
                "Duration": 20,
                "Questions": questions,
            })
    return papers


SAMPLE_PAPERS = build_sample_papers()

if "resources" not in st.session_state:
    st.session_state.resources = DEFAULT_RESOURCES.copy()
if "study_plan" not in st.session_state:
    st.session_state.study_plan = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I am VidyaSpark AI Tutor. Ask me any study question, coding problem, or exam-related doubt."}
    ]
if "reviews" not in st.session_state:
    st.session_state.reviews = [
        {"Name": "Rahul Sharma", "Stream": "B.Tech CSE", "Rating": 5, "Comment": "The clean interface is easy to use and YouTube links open quickly!"},
        {"Name": "Priya Verma", "Stream": "Banking/Railway", "Rating": 5, "Comment": "The AI Doubt Solver is easy to use. Great study app!"},
    ]

# ==========================================
# 4. SIDEBAR NAVIGATION (NO API KEY BOX)
# ==========================================
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <h2>⚡ VidyaSpark</h2>
        <p>India's Smartest AI Study Companion</p>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🔍 Find Resources",
        "🤖 AI Doubt Solver (Gemini)",
        "📝 Timed Sample Papers",
        "📺 YouTube Hub",
        "📌 My Study Plan",
        "➕ Add Resource",
        "⭐ Review & Feedback",
        "ℹ️ About",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("**Developed by:**\n\n**Abhisek Kumar**")
st.sidebar.caption("B.Tech CSE (AI & ML) | Reg: 125433")
st.sidebar.caption("10 Streams: CSE • Mechanical • Electrical • Boards • JEE • NEET • UPSC • SSC • Banking/Railway • SSB")

# ==========================================
# 5. PAGE 1: DASHBOARD (WITH YOUTUBE SEARCH)
# ==========================================
if page == "📊 Dashboard":
    st.markdown(
        """
        <div class="bw-banner">
            <h1>⚡ Welcome to VidyaSpark</h1>
            <p>10 Streams (Incl. Banking & Railway) • Live Gemini AI Doubt Solver • Direct YouTube Study Links</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    total_res = len(st.session_state.resources)
    imp_res = sum(1 for r in st.session_state.resources if r["Important"])
    done_plan = sum(1 for p in st.session_state.study_plan if p["Done"])
    total_plan = len(st.session_state.study_plan)

    with c1:
        st.markdown(f'<div class="bw-metric"><h2>{total_res}</h2><p>Curated Resources</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="bw-metric"><h2>{imp_res}</h2><p>Important Topics</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="bw-metric"><h2>{len(SAMPLE_PAPERS)}</h2><p>Timed Sample Papers</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="bw-metric"><h2>{done_plan}/{total_plan}</h2><p>Study Plan Done</p></div>', unsafe_allow_html=True)

    st.markdown("### 🔥 Must-Study Important Topics (Direct YouTube Search)")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        topic_search = st.text_input(
            "Search any topic to find YouTube lectures",
            placeholder="e.g., Python Loops, DSA, Repo Rate, Thermodynamics, Polity...",
        )
    with col_s2:
        selected_stream = st.selectbox("Filter by Stream", ["All Streams"] + STREAMS)

    if topic_search.strip():
        direct_query = f"{topic_search} {'' if selected_stream == 'All Streams' else selected_stream} full lecture"
        st.markdown(
            f'<div class="bw-card"><b>🎯 YouTube search for:</b> "{topic_search}"</div>',
            unsafe_allow_html=True,
        )
        st.link_button(f"▶️ '{topic_search}' Open on YouTube", yt_search_url(direct_query), use_container_width=True)
        st.write("")

    filtered = [
        r for r in st.session_state.resources
        if r["Important"]
        and (selected_stream == "All Streams" or r["Stream"] == selected_stream)
        and (topic_search.strip().lower() in r["Topic"].lower() or topic_search.strip().lower() in r["Stream"].lower() or not topic_search.strip())
    ]

    if not filtered:
        st.info("No saved topic matched this search. Use the YouTube search button above to find more lectures.")
    else:
        cols = st.columns(2)
        for idx, item in enumerate(filtered):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="bw-card bw-topic-card">
                        <h4 style="margin:0;">📌 {item['Topic']}</h4>
                        <p style="color:#A0A0A0; margin:6px 0 4px 0; font-size:0.9rem;">Stream: {item['Stream']} • Channel: {item['Channel']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.link_button("▶️ Subject Videos", item["URL"], use_container_width=True)
                with b2:
                    st.link_button(
                        "📺 Related Channel",
                        yt_channel_search_url(item["Channel"]),
                        use_container_width=True,
                    )
                with b3:
                    if st.button("➕ Add to Plan", key=f"dash_add_{idx}", use_container_width=True):
                        if not any(p["Topic"] == item["Topic"] for p in st.session_state.study_plan):
                            st.session_state.study_plan.append({"Topic": item["Topic"], "Stream": item["Stream"], "Done": False})
                            st.success("Added to your study plan!")

# ==========================================
# 6. PAGE 2: FIND RESOURCES
# ==========================================
elif page == "🔍 Find Resources":
    st.title("🔍 Find Study Resources")
    q = st.text_input("Search Topic or Subject", placeholder="Enter a topic name...")
    stream_f = st.selectbox("Select Stream", ["All Streams"] + STREAMS)

    matching_resources = [
        r for r in st.session_state.resources
        if (stream_f == "All Streams" or r["Stream"] == stream_f)
        and (q.lower() in r["Topic"].lower() or q.lower() in r["Channel"].lower())
    ]

    if not matching_resources:
        st.info("No resources found. Try another topic or stream.")
    else:
        for idx, r in enumerate(matching_resources):
            st.markdown(
                f"<div class='bw-card'><b>{r['Topic']}</b> — {r['Stream']} <span style='color:#FFFFFF;'>({r['Channel']})</span></div>",
                unsafe_allow_html=True,
            )
            col_youtube, col_channel, col_guide = st.columns([1, 1, 1])
            with col_youtube:
                st.link_button("▶️ Subject Videos", r["URL"], use_container_width=True)
            with col_channel:
                st.link_button(
                    "📺 Related Channel",
                    yt_channel_search_url(r["Channel"]),
                    use_container_width=True,
                )
            with col_guide:
                guide_key = f"study_guide_{idx}_{r['Topic']}"
                if st.button("✨ AI Study Guide", key=f"guide_btn_{idx}_{r['Topic']}", use_container_width=True):
                    guide_prompt = (
                        f"Create a detailed but easy-to-follow study guide for the subject/topic: {r['Topic']}. "
                        f"Student stream: {r['Stream']}. Recommended source/channel listed: {r['Channel']}. "
                        "Include: (1) a short introduction, (2) key chapters/subtopics in a sensible learning order, "
                        "(3) recommended learning sources and what each is useful for (include YouTube channel names, "
                        "websites, or textbooks only when you know relevant ones; do not invent specific video links), "
                        "(4) a beginner-to-advanced roadmap, (5) practice questions or project ideas, and "
                        "(6) study tips. Use clear English, headings, and concise bullet points."
                    )
                    with st.spinner("Generating your study guide..."):
                        st.session_state[guide_key] = ask_gemini(guide_prompt, r["Stream"], "English")
            if guide_key in st.session_state:
                with st.expander(f"AI Study Guide: {r['Topic']}", expanded=True):
                    st.markdown(st.session_state[guide_key])

# ==========================================
# 7. PAGE 3: AI DOUBT SOLVER (HIDDEN KEY)
# ==========================================
elif page == "🤖 AI Doubt Solver (Gemini)":
    st.title("🤖 AI Doubt Solver (Powered by Gemini)")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        ai_stream = st.selectbox("Select Your Stream / Exam", STREAMS)
    with c2:
        ai_lang = st.selectbox("Answer Language", ["English", "Hindi"])
    with c3:
        st.write("")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Chat cleared. Ask a new question!"}
            ]
            st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_q = st.chat_input("Enter your question (e.g., explain Python loops or the Repo Rate)...")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        with st.chat_message("assistant"):
            with st.spinner("VidyaSpark AI is thinking..."):
                reply = ask_gemini(user_q, ai_stream, ai_lang)
                st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ==========================================
# 8. PAGE 4: TIMED SAMPLE PAPERS
# ==========================================
elif page == "📝 Timed Sample Papers":
    st.title("📝 Timed Sample Papers")
    selected_stream = st.selectbox("Select Subject / Stream", STREAMS, key="mock_stream_filter")
    stream_papers = [p for p in SAMPLE_PAPERS if p["Stream"] == selected_stream]
    paper_titles = [p["Title"] for p in stream_papers]
    selected_title = st.selectbox("Select Mock Test", paper_titles)
    paper = next(p for p in stream_papers if p["Title"] == selected_title)

    st.info(f"Stream: {paper['Stream']} | Questions: {len(paper['Questions'])} | Suggested Time: {paper['Duration']} Minutes")
    st.caption("Choose one answer for every question. No answer is selected by default.")
    answers = {}
    for i, (q_text, opts, ans) in enumerate(paper["Questions"]):
        answers[i] = st.radio(f"Q{i+1}. {q_text}", opts, index=None, key=f"q_{selected_title}_{i}")

    if st.button("✅ Submit Test"):
        unanswered = [i + 1 for i, answer in answers.items() if answer is None]
        if unanswered:
            st.warning(f"Please answer all questions before submitting. Unanswered: {len(unanswered)}")
        else:
            score = sum(1 for i, (_, _, ans) in enumerate(paper["Questions"]) if answers[i] == ans)
            st.success(f"Your score: {score} / {len(paper['Questions'])}")
            with st.expander("Review answers"):
                for i, (q_text, _, correct_answer) in enumerate(paper["Questions"]):
                    result = "✅" if answers[i] == correct_answer else "❌"
                    st.write(f"{result} Q{i + 1}. {q_text} — Correct answer: **{correct_answer}**")

# ==========================================
# 9. PAGE 5: YOUTUBE HUB
# ==========================================
elif page == "📺 YouTube Hub":
    st.title("📺 YouTube Study Hub")
    yt_q = st.text_input("Enter a topic to find YouTube lectures", placeholder="e.g., C Programming pointers in Hindi")
    yt_lang = st.selectbox("Preferred Language", ["English", "Hindi"])
    if yt_q.strip():
        st.link_button(f"▶️ Open '{yt_q}' on YouTube", yt_search_url(f"{yt_q} {yt_lang} tutorial"), use_container_width=True)
    yt_channel = st.text_input("Find a related YouTube channel", placeholder="e.g., CodeWithHarry, Physics Wallah")
    if yt_channel.strip():
        st.link_button(
            f"📺 Search '{yt_channel}' channel on YouTube",
            yt_channel_search_url(yt_channel),
            use_container_width=True,
        )

# ==========================================
# 10. PAGE 6: MY STUDY PLAN
# ==========================================
elif page == "📌 My Study Plan":
    st.title("📌 My Study Plan")
    new_task = st.text_input("Add a new study target")
    if st.button("➕ Add Target") and new_task.strip():
        st.session_state.study_plan.append({"Topic": new_task.strip(), "Stream": "Custom", "Done": False})
        st.rerun()

    if not st.session_state.study_plan:
        st.info("Your study plan is empty. Add topics from the Dashboard or enter a target above.")
    else:
        for i, task in enumerate(st.session_state.study_plan):
            checked = st.checkbox(f"{task['Topic']} ({task['Stream']})", value=task["Done"], key=f"plan_{i}")
            st.session_state.study_plan[i]["Done"] = checked

# ==========================================
# 11. PAGE 7: ADD RESOURCE
# ==========================================
elif page == "➕ Add Resource":
    st.title("➕ Add New Study Resource")
    with st.form("add_res_form"):
        t_name = st.text_input("Topic Name")
        t_stream = st.selectbox("Stream", STREAMS)
        t_channel = st.text_input("YouTube Channel / Source")
        t_url = st.text_input("YouTube Link (Optional — a search link will be generated if left blank)")
        submitted = st.form_submit_button("Save Resource")
        if submitted and t_name.strip():
            final_url = t_url.strip() if t_url.strip() else yt_search_url(f"{t_name} {t_channel}")
            st.session_state.resources.append({
                "Topic": t_name.strip(),
                "Stream": t_stream,
                "Channel": t_channel.strip() or "YouTube",
                "Important": True,
                "URL": final_url,
            })
            st.success("Resource added successfully!")

# ==========================================
# 12. PAGE 8: REVIEW & FEEDBACK FORM
# ==========================================
elif page == "⭐ Review & Feedback":
    st.title("⭐ Review & Feedback Form")
    st.write("Share your review and feedback to help us improve VidyaSpark!")

    with st.form("review_form", clear_on_submit=True):
        r_name = st.text_input("Your Name *", placeholder="e.g., Aman Verma")
        r_stream = st.selectbox("Your Stream / Exam", STREAMS)
        r_rating = st.slider("Rate this app (1 = Poor, 5 = Excellent)", 1, 5, 5)
        r_comment = st.text_area("Your Feedback / Suggestion *", placeholder="What did you think of the app? What features should we add?")
        submit_review = st.form_submit_button("🚀 Submit Review")

        if submit_review:
            if not r_name.strip() or not r_comment.strip():
                st.error("Please enter both your name and feedback.")
            else:
                st.session_state.reviews.insert(0, {
                    "Name": r_name.strip(),
                    "Stream": r_stream,
                    "Rating": r_rating,
                    "Comment": r_comment.strip(),
                })
                st.success("Thank you! Your review has been submitted successfully.")

    st.divider()
    st.subheader("💬 Recent Student Reviews")
    for rev in st.session_state.reviews:
        stars = "⭐" * rev["Rating"]
        st.markdown(
            f"""
            <div class="bw-card">
                <h4 style="margin:0;">{rev['Name']} <span style="font-size:0.85rem; color:#A0A0A0;">({rev['Stream']})</span></h4>
                <p style="margin:4px 0;">{stars}</p>
                <p style="margin:0; color:#D5D5D5;">"{rev['Comment']}"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================
# 13. PAGE 9: ABOUT PROJECT
# ==========================================
elif page == "ℹ️ About":
    st.title("ℹ️ About VidyaSpark")
    st.markdown(
        """
        <div class="bw-card">
            <h3>⚡ VidyaSpark - AI Study Resource Recommendation System</h3>
            <p><b>Developed by:</b> Abhisek Kumar</p>
            <p><b>Course:</b> B.Tech CSE (AI & ML) | <b>Reg No:</b> 125433</p>
            <p><b>Features:</b> 10 Academic & Competitive Exam Streams, Direct YouTube Search Links, Live Gemini AI Doubt Solver (Hidden API Key), Timed Mock Tests, Study Planner, and Student Review System.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
