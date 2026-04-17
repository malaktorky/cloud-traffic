import streamlit as st

st.set_page_config(page_title="Traffic Assistant", layout="centered")

st.title("🚦 Smart Traffic Assistant")

WELCOME_MESSAGE = """Hello. I can help you with traffic status.

Try asking:

- Best road now
- Road 1 status
- Road 2 status
- Road 3 status
- Is there any incident?
- Traffic summary
"""

# حفظ المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

# عرض الرسائل القديمة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# إدخال المستخدم
user_input = st.chat_input("Ask about traffic...")

def generate_response(user_text):
    text = user_text.lower().strip()

    if "best road" in text or text == "best road now" or "best" in text:
        return "✅ Best road now: Road 1."

    elif "road 1" in text:
        return "Road 1 status: LOW congestion, 8 vehicles, no incident."

    elif "road 2" in text:
        return "Road 2 status: MEDIUM congestion, 18 vehicles, no incident."

    elif "road 3" in text:
        return "Road 3 status: HIGH congestion, suspected incident detected. Avoid this road."

    elif "incident" in text or "accident" in text:
        return "🚨 Yes. A suspected incident is detected on Road 3."

    elif "traffic summary" in text or "summary" in text or "traffic" in text:
        return (
            "Traffic summary:\n"
            "- Road 1: LOW congestion\n"
            "- Road 2: MEDIUM congestion\n"
            "- Road 3: HIGH congestion with suspected incident"
        )

    else:
        return (
            "I can answer these questions:\n"
            "- Best road now\n"
            "- Road 1 status\n"
            "- Road 2 status\n"
            "- Road 3 status\n"
            "- Is there any incident?\n"
            "- Traffic summary"
        )

# معالجة السؤال الجديد
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    response = generate_response(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()