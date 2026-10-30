from mcp.server.mcpserver import MCPServer

# إنشاء خادم MCP باسم مساعد الطالب
mcp = MCPServer("StudentAssistant")

# ==========================================
# 1. Resources (الموارد المرجعية)
# ==========================================
ACADEMIC_CALENDAR = """
التقويم الجامعي للفصل الحالي:
- بداية الفصل الدراسي: 25 أغسطس
- فترة الاختبارات النصفية: 20 أكتوبر إلى 31 أكتوبر
- آخر موعد لتقديم المشاريع: 15 ديسمبر
- بداية الاختبارات النهائية: 20 ديسمبر
"""

@mcp.resource("academic://calendar")
def get_academic_calendar() -> str:
    """إرجاع جدول التقويم الأكاديمي للجامعة كمصدر مرجعي"""
    return ACADEMIC_CALENDAR


# ==========================================
# 2. Tools (الأدوات البرمجية)
# ==========================================
@mcp.tool()
def calculate_gpa(total_points: float, total_credit_hours: float) -> str:
    """حساب المعدل التراكمي الجامعي من 5 بناءً على مجموع النقاط وساعات المواد"""
    if total_credit_hours <= 0:
        return "خطأ: مجموع الساعات يجب أن يكون أكبر من صفر."
    gpa = total_points / total_credit_hours
    return f"المعدل التراكمي المحسوب هو: {round(gpa, 2)} من 5.0"

@mcp.tool()
def add_assignment(subject: str, task_title: str, due_date: str) -> str:
    """أداة لجدولة وحفظ الواجبات والمهام الدراسية للطالب"""
    return f"تمت إضافة المهمة بنجاح: '{task_title}' لمادة ({subject}) بتاريخ تسليم: {due_date}."


# ==========================================
# 3. Prompts (قوالب التوجيه الجاهزة)
# ==========================================
@mcp.prompt()
def study_plan_prompt(subject_name: str, days_left: int) -> str:
    """قالب لتوليد خطة مذاكرة ذكية للمادة حسب الأيام المتبقية"""
    return (
        f"أنت مستشار أكاديمي خبير. ضع جدول مذاكرة مكثف ومنظم لمادة '{subject_name}' "
        f"بحيث يغطي كل الفصول خلال {days_left} أيام المتبقية قبل الاختبار، "
        f"مع تخصيص وقت للمراجعة وحل الأسئلة السابقة."
    )

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000
    )