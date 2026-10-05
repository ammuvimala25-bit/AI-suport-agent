import os
import json
import re
import base64
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

APP_TITLE = "Vimala AI Support Agent"

MODEL = os.getenv(
    "MODEL",
    "Qwen/Qwen3.8-27B"
).strip()

HF_TOKEN = os.getenv(
    "HF_TOKEN",
    ""
).strip()

SERPAPI_KEY = os.getenv(
    "SERPAPI_KEY",
    ""
).strip()

KNOWLEDGE_FOLDER = "knowledge_base"
MEMORY_FILE = "customer_memory.json"
TICKET_FILE = "tickets.json"
BACKGROUND_IMAGE = "background.jpg"


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# BACKGROUND
# =========================================================

def load_background():

    if not os.path.exists(BACKGROUND_IMAGE):
        return ""

    try:
        with open(
            BACKGROUND_IMAGE,
            "rb"
        ) as f:
            return base64.b64encode(
                f.read()
            ).decode()

    except Exception:
        return ""


bg = load_background()


if bg:

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image:
            linear-gradient(
                rgba(255,255,255,0.60),
                rgba(255,255,255,0.60)
            ),
            url(
                "data:image/jpeg;base64,{bg}"
            );

            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        """
        <style>

        .stApp {
            background:
            linear-gradient(
                135deg,
                #fff8fb,
                #f7f2ff
            );
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# UI CSS
# =========================================================

st.markdown(
    """
<style>

/* MAIN */

.block-container {
    padding-top: 45px;
    padding-bottom: 30px;
    max-width: 1100px;
}


/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(12px);
}


/* TITLE */

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #252a36;
    margin-bottom: 22px;
}


/* ONLINE BOX */

.online-box {
    background: rgba(225,248,232,0.92);
    border: 1px solid #bce7c8;
    border-radius: 8px;
    padding: 16px 20px;
    color: #16803c;
    font-size: 16px;
}


/* GREEN DOT */

.online-dot {
    display: inline-block;
    width: 19px;
    height: 19px;
    background: #16c63b;
    border-radius: 50%;
    margin-right: 9px;
    vertical-align: -3px;
    box-shadow: 0 0 8px rgba(22,198,59,0.35);
}


/* FEATURE */

.feature-box {
    margin-top: 15px;
    padding: 15px 18px;
    border-radius: 10px;
    background: rgba(255,255,255,0.72);
    color: #555a65;
    font-size: 14px;
}


/* CHAT */

.chat-box {
    margin-top: 18px;
    min-height: 390px;
    padding: 20px;
    border-radius: 18px;
    background: rgba(255,255,255,0.48);
    border: 1px solid rgba(255,255,255,0.80);
}


/* USER */

.user-msg {
    background: white;
    padding: 12px 16px;
    border-radius: 16px;
    margin: 10px 0 10px auto;
    max-width: 75%;
    color: #30343c;
}


/* AI */

.ai-msg {
    background: rgba(239,233,255,0.94);
    padding: 12px 16px;
    border-radius: 16px;
    margin: 10px auto 10px 0;
    max-width: 80%;
    color: #30343c;
}


/* SIDEBAR HEADINGS */

.side-title {
    font-size: 21px;
    font-weight: 700;
    color: #30343e;
    margin-bottom: 18px;
}

.side-section {
    font-size: 18px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 10px;
}


/* MEMORY */

.memory-card {
    padding: 12px;
    border-radius: 12px;
    background: rgba(241,235,255,0.90);
    border: 1px solid #ddd2fa;
}


/* BUTTON */

.stButton > button {
    width: 100%;
    border-radius: 8px;
}


/* INPUT */

.stTextInput input {
    background: rgba(255,255,255,0.92) !important;
}


/* HIDE STREAMLIT */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# JSON
# =========================================================

def load_json(
    filename,
    default
):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return default


def save_json(
    filename,
    data
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# KNOWLEDGE FILES
# =========================================================

def count_knowledge_files():

    if not os.path.exists(
        KNOWLEDGE_FOLDER
    ):
        return 0

    count = 0

    for root, dirs, files in os.walk(
        KNOWLEDGE_FOLDER
    ):

        for file in files:

            if file.lower().endswith(
                (
                    ".txt",
                    ".pdf",
                    ".csv",
                    ".md"
                )
            ):

                count += 1

    return count


# =========================================================
# LONG TERM MEMORY
# =========================================================

def get_memory(
    customer_id
):

    database = load_json(
        MEMORY_FILE,
        {}
    )

    if customer_id not in database:

        database[customer_id] = {
            "name": "",
            "email": "",
            "phone": "",
            "preferences": [],
            "previous_issues": [],
            "important_information": [],
            "conversation_summary": "",
            "last_updated": ""
        }

        save_json(
            MEMORY_FILE,
            database
        )

    return database[customer_id]


def update_memory(
    customer_id,
    data
):

    database = load_json(
        MEMORY_FILE,
        {}
    )

    if customer_id not in database:

        database[customer_id] = get_memory(
            customer_id
        )

    memory = database[customer_id]

    for key in [
        "name",
        "email",
        "phone",
        "conversation_summary"
    ]:

        if data.get(key):

            memory[key] = data[key]

    for key in [
        "preferences",
        "previous_issues",
        "important_information"
    ]:

        values = data.get(
            key,
            []
        )

        if isinstance(
            values,
            str
        ):
            values = [values]

        for value in values:

            if (
                value
                and value not in memory[key]
            ):

                memory[key].append(
                    value
                )

    memory["last_updated"] = (
        datetime.now().isoformat()
    )

    database[customer_id] = memory

    save_json(
        MEMORY_FILE,
        database
    )


# =========================================================
# TICKET
# =========================================================

def create_ticket(
    customer_id,
    issue
):

    tickets = load_json(
        TICKET_FILE,
        []
    )

    ticket_id = (
        f"VIM-{len(tickets)+1:05d}"
    )

    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "status": "Open",
        "priority": "High",
        "created_at":
            datetime.now().isoformat()
    }

    tickets.append(ticket)

    save_json(
        TICKET_FILE,
        tickets
    )

    return ticket


# =========================================================
# AI CHAT
# =========================================================

def ask_ai(
    messages
):

    if not HF_TOKEN:

        return (
            "⚠️ HF_TOKEN is missing "
            "in your .env file."
        )

    headers = {
        "Authorization":
            f"Bearer {HF_TOKEN}",
        "Content-Type":
            "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 500
    }

    try:

        response = requests.post(

            "https://router.huggingface.co/v1/chat/completions",

            headers=headers,

            json=payload,

            timeout=90
        )

        if response.status_code != 200:

            return (
                f"⚠️ AI API Error "
                f"{response.status_code}\n\n"
                f"{response.text[:500]}"
            )

        result = response.json()

        return (
            result["choices"][0]
            ["message"]
            ["content"]
            .strip()
        )

    except Exception as e:

        return (
            f"⚠️ AI Error: {e}"
        )


# =========================================================
# SUPPORT AGENT
# =========================================================

def support_agent(
    customer_id,
    question
):

    memory = get_memory(
        customer_id
    )

    system_prompt = f"""

You are Vimala AI Support Agent.

Customer ID:
{customer_id}

Long-term customer memory:

{json.dumps(
    memory,
    ensure_ascii=False,
    indent=2
)}

Your job is customer support.

Rules:

- Be friendly.
- Be concise.
- Use customer memory when useful.
- Do not invent information.
- If you don't know, say you don't know.
- Never request passwords.
- Never request OTP.
- Never request CVV.
- Never request full card numbers.
- If customer asks for a human agent,
  help with escalation.
- If customer asks for a ticket,
  create a ticket.
- Keep normal answers short.

"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for msg in st.session_state.messages[-8:]:

        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": question
    })

    return ask_ai(
        messages
    )


# =========================================================
# HUMAN REQUEST
# =========================================================

def wants_human(
    text
):

    text = text.lower()

    keywords = [
        "human",
        "agent",
        "person",
        "real person",
        "customer care",
        "customer service",
        "representative",
        "support executive"
    ]

    return any(
        word in text
        for word in keywords
    )


# =========================================================
# TICKET REQUEST
# =========================================================

def wants_ticket(
    text
):

    text = text.lower()

    keywords = [
        "create ticket",
        "raise ticket",
        "support ticket",
        "complaint",
        "complain",
        "escalate",
        "issue not solved"
    ]

    return any(
        word in text
        for word in keywords
    )


# =========================================================
# SESSION
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "customer_id" not in st.session_state:

    st.session_state.customer_id = (
        "customer001"
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="side-title">⚙️ Agent Controls</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"**Knowledge Files:** "
        f"{count_knowledge_files()}"
    )

    st.write(
        f"**AI Model:** "
        f"{MODEL}"
    )

    st.divider()

    # CUSTOMER

    st.markdown(
        '<div class="side-section">👤 Customer</div>',
        unsafe_allow_html=True
    )

    customer_id = st.text_input(
        "Customer ID",
        value=st.session_state.customer_id
    )

    customer_id = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        customer_id
    )

    st.session_state.customer_id = (
        customer_id
    )

    st.divider()

    # PRODUCT

    st.markdown(
        '<div class="side-section">🔎 Online Product Search</div>',
        unsafe_allow_html=True
    )

    product_name = st.text_input(
        "Product name",
        placeholder="Example: Hair Oil"
    )

    if st.button(
        "Search Product"
    ):

        if not SERPAPI_KEY:

            st.warning(
                "SERPAPI_KEY missing."
            )

        elif product_name:

            params = {
                "engine": "google",
                "q": product_name,
                "api_key": SERPAPI_KEY,
                "num": 5
            }

            try:

                r = requests.get(
                    "https://serpapi.com/search.json",
                    params=params,
                    timeout=30
                )

                if r.status_code == 200:

                    data = r.json()

                    results = data.get(
                        "organic_results",
                        []
                    )

                    st.session_state.product_results = (
                        results
                    )

                    st.success(
                        "Product search completed."
                    )

                else:

                    st.error(
                        "Product search failed."
                    )

            except Exception as e:

                st.error(
                    str(e)
                )

    # TNPSC

    st.markdown(
        '<div class="side-section">📚 TNPSC Books</div>',
        unsafe_allow_html=True
    )

    tnpsc_query = st.text_input(
        "Search TNPSC books",
        placeholder="Example: Group 4 Tamil"
    )

    if st.button(
        "Search TNPSC Books"
    ):

        if not SERPAPI_KEY:

            st.warning(
                "SERPAPI_KEY missing."
            )

        elif tnpsc_query:

            params = {
                "engine": "google",
                "q":
                    f"TNPSC {tnpsc_query} books",
                "api_key": SERPAPI_KEY,
                "num": 5
            }

            try:

                r = requests.get(
                    "https://serpapi.com/search.json",
                    params=params,
                    timeout=30
                )

                if r.status_code == 200:

                    data = r.json()

                    st.session_state.tnpsc_results = (
                        data.get(
                            "organic_results",
                            []
                        )
                    )

                    st.success(
                        "TNPSC search completed."
                    )

                else:

                    st.error(
                        "TNPSC search failed."
                    )

            except Exception as e:

                st.error(
                    str(e)
                )

    # MEMORY

    st.markdown(
        '<div class="side-section">🧠 Long-Term Memory</div>',
        unsafe_allow_html=True
    )

    memory = get_memory(
        customer_id
    )

    if memory.get("name"):

        st.markdown(
            f"""
            <div class="memory-card">

            <b>👤 {memory["name"]}</b>

            <br>

            Memory active

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.caption(
            "Customer memory will be saved automatically."
        )

    if st.button(
        "🗑️ Clear Chat"
    ):

        st.session_state.messages = []

        st.rerun()


# =========================================================
# MAIN TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🤖 Vimala AI Support Agent</div>',
    unsafe_allow_html=True
)


# =========================================================
# ONLINE STATUS
# =========================================================

st.markdown(
    """
    <div class="online-box">
        <span class="online-dot"></span>
        AI Customer Support Agent is Online
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FEATURES
# =========================================================

st.markdown(
    """
    <div class="feature-box">
        RAG · Online Product Search · TNPSC Books ·
        Tickets · Human Escalation · Long-Term Memory
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SEARCH RESULTS
# =========================================================

if "product_results" in st.session_state:

    with st.expander(
        "🔎 Product Search Results"
    ):

        for item in st.session_state.product_results:

            st.markdown(
                f"### {item.get('title','')}"
            )

            st.write(
                item.get(
                    "snippet",
                    ""
                )
            )

            if item.get("link"):

                st.write(
                    item["link"]
                )


if "tnpsc_results" in st.session_state:

    with st.expander(
        "📚 TNPSC Search Results"
    ):

        for item in st.session_state.tnpsc_results:

            st.markdown(
                f"### {item.get('title','')}"
            )

            st.write(
                item.get(
                    "snippet",
                    ""
                )
            )

            if item.get("link"):

                st.write(
                    item["link"]
                )


# =========================================================
# CHAT
# =========================================================

st.markdown(
    '<div class="chat-box">',
    unsafe_allow_html=True
)

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="user-msg">
                <b>👤 You</b><br><br>
                {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="ai-msg">
                <b>🤖 Vimala AI</b><br><br>
                {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask your customer support question..."
)


if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    # HUMAN

    if wants_human(question):

        answer = (
            "👨‍💼 I can help you connect "
            "with a human support agent. "
            "Please describe your issue and "
            "I can create a support ticket."
        )

    # TICKET

    elif wants_ticket(question):

        ticket = create_ticket(
            customer_id,
            question
        )

        update_memory(
            customer_id,
            {
                "previous_issues": [
                    question
                ]
            }
        )

        answer = (
            "🎫 **Support ticket created!**\n\n"
            f"Ticket ID: **{ticket['ticket_id']}**\n\n"
            "Status: **Open**\n\n"
            "Priority: **High**"
        )

    # AI

    else:

        with st.spinner(
            "🤖 Vimala AI is thinking..."
        ):

            answer = support_agent(
                customer_id,
                question
            )

        update_memory(
            customer_id,
            {
                "previous_issues": [
                    question
                ]
            }
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:25px;
        color:#777;
        font-size:13px;
    ">
        🧠 Long-Term Memory Enabled
        &nbsp; • &nbsp;
        🎫 Ticket System
        &nbsp; • &nbsp;
        👨‍💼 Human Escalation
    </div>
    """,
    unsafe_allow_html=True
)