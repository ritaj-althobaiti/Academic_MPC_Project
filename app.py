import streamlit as st
import asyncio
from mcp import Client
MCP_URL = "http://127.0.0.1:8000/mcp"

async def call_mcp_tool(tool_name, arguments):
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, arguments)
        return "\n".join(
            item.text for item in result.content
            if hasattr(item, "text")
        )

async def read_mcp_resource(resource_uri):
    async with Client(MCP_URL) as client:
        result = await client.read_resource(resource_uri)
        return "\n".join(
            item.text for item in result.contents
            if hasattr(item, "text")
        )

async def get_mcp_prompt(prompt_name, arguments):
    async with Client(MCP_URL) as client:
        return await client.get_prompt(prompt_name, arguments)

st.set_page_config(page_title="Academic AI Assistant (MCP)", page_icon="🎓")
st.title("🎓 مساعد الطالب الذكي (نظام MCP)")
st.caption("AI Agent تفاعلي مدعوم ببروتوكول MCP: أدوات، تقويم، وقوالب دراسية")

# إدارة حالة المحادثة المتعددة الخطوات
if "step" not in st.session_state:
    st.session_state.step = "idle"
if "temp_data" not in st.session_state:
    st.session_state.temp_data = {}

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "أهلاً بك! أنا وكيلك الأكاديمي الذكي المدعوم بـ MCP.\n\nكيف يمكنني مساعدتك اليوم؟\n- عرض التقويم الأكاديمي\n- إضافة واجب دراسي جديد\n- إنشاء خطة مذاكرة لمادة\n- حساب المعدل التراكمي"
        }
    ]

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# استقبال إدخال المستخدم
if user_prompt := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    response = ""
    text = user_prompt.strip()

    # --- مسار 1: إدارة خطوات إضافة واجب ---
    if st.session_state.step == "waiting_subject":
        st.session_state.temp_data["subject"] = text
        st.session_state.step = "waiting_task"
        response = f"تمام لمادة ({text})! ما هو عنوان أو تفاصيل الواجب؟"

    elif st.session_state.step == "waiting_task":
        st.session_state.temp_data["task"] = text
        st.session_state.step = "waiting_date"
        response = "ممتاز، وما هو تاريخ أو موعد التسليم؟ (مثال: الخميس القادم، أو 25 نوفمبر)"

    elif st.session_state.step == "waiting_date":
        due_date = text
        subject = st.session_state.temp_data["subject"]
        task = st.session_state.temp_data["task"]
        # استدعاء الأداة من خادم MCP
        result = asyncio.run(call_mcp_tool(
            "add_assignment",
            {"subject": subject, "task_title": task, "due_date": due_date}
        ))
        response = f"✅ **[تم استدعاء Tool: add_assignment بنجاح]**\n\n{result}"
        st.session_state.step = "idle"
        st.session_state.temp_data = {}

    # --- مسار 2: إدارة خطوات خطة المذاكرة ---
    elif st.session_state.step == "waiting_plan_subject":
        st.session_state.temp_data["plan_subject"] = text
        st.session_state.step = "waiting_plan_days"
        response = f"حسناً لمادة ({text})، كم يوماً متبقياً لديك قبل موعد الاختبار؟"

    elif st.session_state.step == "waiting_plan_days":
        try:
            days = int(text)
            subject = st.session_state.temp_data["plan_subject"]
            prompt_instruction = asyncio.run(get_mcp_prompt(
                "study_plan_prompt",
                {"subject_name": subject, "days_left": days}
            ))

            # توليد الخطة الدراسية التفصيلية بناءً على القالب
            response = (
                f"📋 **[تطبيق Prompt Template: study_plan_prompt]**\n\n"
                f"تم بناء خطة المذاكرة لمادة **{subject}** خلال **{days} أيام**:\n\n"
            )
            for d in range(1, days + 1):
                if d == days:
                    response += f"- **اليوم {d}:** مراجعة عامة شاملة، وحل نماذج اختبارات سابقة.\n"
                elif d == 1:
                    response += f"- **اليوم {d}:** مراجعة المفاهيم الأساسية والفصول الأولى وتلخيص النقاط المهمة.\n"
                else:
                    response += f"- **اليوم {d}:** دراسة الفصول المتقدمة والتطبيقات العملية والتمارين.\n"

            st.session_state.step = "idle"
            st.session_state.temp_data = {}
        except ValueError:
            response = "يرجى كتابة عدد الأيام كأرقام فقط (مثلاً: 3 أو 5)."

    # --- مسار 3: إدارة خطوات حساب المعدل ---
    elif st.session_state.step == "waiting_points":
        st.session_state.temp_data["points"] = text
        st.session_state.step = "waiting_hours"
        response = "كم مجموع الساعات المعتمدة لهذه المواد؟"

    elif st.session_state.step == "waiting_hours":
        try:
            points = float(st.session_state.temp_data["points"])
            hours = float(text)
            result = asyncio.run(call_mcp_tool(
                "calculate_gpa",
                {"total_points": points, "total_credit_hours": hours}
            ))
            response = f"📊 **[تم استدعاء Tool: calculate_gpa]**\n\n{result}"
            st.session_state.step = "idle"
            st.session_state.temp_data = {}
        except ValueError:
            response = "يرجى كتابة أرقام صحيحة للنقاط والساعات."

    # --- القائمة المباشرة والأوامر العامة ---
    else:
        text_lower = text.lower()

        if "تقويم" in text_lower or "مواعيد" in text_lower:
            data = asyncio.run(read_mcp_resource("academic://calendar"))
            response = f"📅 **[استدعاء Resource: academic://calendar]**\n\n{data}"

        elif "واجب" in text_lower or "مهمة" in text_lower:
            st.session_state.step = "waiting_subject"
            response = "بالتأكيد! ما اسم المادة التي تريد إضافة واجب لها؟"

        elif "خطة" in text_lower or "مذاكرة" in text_lower:
            st.session_state.step = "waiting_plan_subject"
            response = "ممتاز، سأساعدك في تنظيم وقتك! ما اسم المادة التي تريد وضع خطة لها؟"

        elif "معدل" in text_lower or "gpa" in text_lower:
            st.session_state.step = "waiting_points"
            response = "لحساب معدلك بدقة، كم مجموع النقاط التي حصلت عليها؟"

        else:
            response = (
                "أنا وكيلك الأكاديمي، يمكنك الاختيار مما يلي:\n"
                "1. **عرض التقويم:** اكتب 'اعرض التقويم'.\n"
                "2. **إضافة واجب:** اكتب 'أضف واجب' وسأسألك عن بياناته.\n"
                "3. **خطة مذاكرة:** اكتب 'خطة مذاكرة' وسأصيغ جدولاً لأيامك.\n"
                "4. **حساب المعدل:** اكتب 'احسب معدلي'."
            )

    with st.chat_message("assistant"):
        st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})