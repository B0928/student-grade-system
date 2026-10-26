"""
教务管理系统 - 控制台入口
负责：用户交互（input/print）和菜单逻辑
业务逻辑全部调用 GradeSystem 的方法
"""

import time
from grade_system2 import GradeSystem


def input_float(prompt: str) -> float:
    """安全地读取一个浮点数，输入非法就一直让用户重输"""
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("输入无效，请输入数字。")


def confirm(prompt: str) -> bool:
    """读取 yes/no 确认"""
    ans = input(f"{prompt}（y/n）：").strip().lower()
    return ans in ("y", "yes", "是")


def show_menu(system: GradeSystem) -> None:
    print()
    print("#" * 60)
    print(f"  {system.SYSTEM_NAME} v{system.SYSTEM_VERSION}")
    print("#" * 60)
    print("  1. 添加学生")
    print("  2. 修改学生成绩")
    print("  3. 删除学生")
    print("  4. 查询学生")
    print("  5. 显示所有学生")
    print("  6. 班级统计（平均分 / 及格率 / 排名）")
    print("  7. 生成 Excel 表格")
    print("  8. 生成成绩分布图")
    print("  9. 保存数据")
    print(" 10. 退出系统")
    print("#" * 60)


def pick_student(system: GradeSystem, action: str):
    """按学号或姓名定位学生；重名时列出学号让用户选。没找到返回 None"""
    key = input(f"请输入要{action}的学生学号或姓名：").strip()
    stu = system.find_by_id(key)
    if stu is not None:
        return stu
    matches = system.find_all_by_name(key)
    if not matches:
        print(f"未找到学生：{key}")
        return None
    if len(matches) == 1:
        return matches[0]
    print(f"找到 {len(matches)} 个同名学生，请按学号选择：")
    for s in matches:
        print(f"  {s}")
    sid = input("请输入学号：").strip()
    stu = system.find_by_id(sid)
    if stu is None:
        print(f"未找到学号：{sid}")
    return stu


def do_add(system: GradeSystem) -> None:
    print("\n--- 添加学生 ---")
    name = input("请输入学生姓名：").strip()
    if not name:
        print("姓名不能为空。")
        return

    chinese = input_float("请输入语文成绩：")
    math = input_float("请输入数学成绩：")
    english = input_float("请输入英语成绩：")
    student_id = input("请输入学号（直接回车自动生成）：").strip() or None

    try:
        ok = system.add_student(name, chinese, math, english, student_id=student_id)
        if ok:
            stu = system.find_all_by_name(name)[-1]
            print(f"学生 {name} 添加成功！学号：{stu.student_id}")
        else:
            print(f"添加失败：学号 {student_id} 已存在。")
    except ValueError as e:
        print(f"添加失败：{e}")


def do_update(system: GradeSystem) -> None:
    print("\n--- 修改学生成绩 ---")
    stu = pick_student(system, "修改")
    if stu is None:
        return

    print(f"当前成绩：{stu}")
    while True:
        subject = input("请输入要修改的科目（语文/数学/英语），输入 q 退出：").strip()
        if subject.lower() == "q":
            break
        if subject not in ("语文", "数学", "英语"):
            print("科目无效，请输入 语文/数学/英语。")
            continue

        score = input_float(f"请输入新的{subject}成绩：")
        try:
            stu.update_score(subject, score)
            print(f"{subject}成绩修改成功！")
            print(f"修改后：{stu}")
        except ValueError as e:
            print(f"修改失败：{e}")

        if not confirm("继续修改其他科目"):
            break


def do_delete(system: GradeSystem) -> None:
    print("\n--- 删除学生 ---")
    stu = pick_student(system, "删除")
    if stu is None:
        return

    print(f"将删除：{stu}")
    if not confirm("确认删除"):
        print("已取消。")
        return

    system.delete_student_by_id(stu.student_id)
    print(f"学生 {stu.name}（学号 {stu.student_id}）已删除。")


def do_query(system: GradeSystem) -> None:
    print("\n--- 查询学生 ---")
    stu = pick_student(system, "查询")
    if stu is not None:
        print(stu)


def do_show_all(system: GradeSystem) -> None:
    print("\n--- 所有学生 ---")
    students = system.get_all_students()
    if not students:
        print("（暂无学生数据）")
        return
    print(f"共 {len(students)} 名学生：")
    print("-" * 80)
    for i, stu in enumerate(students, 1):
        print(f"{i:>2}. {stu}")
    print("-" * 80)


def do_stats(system: GradeSystem) -> None:
    print("\n--- 班级统计 ---")
    if system.student_count() == 0:
        print("（暂无学生数据）")
        return

    avg = system.class_average()
    passed = system.pass_rate()
    rank = system.rank_by_total()

    print(f"学生人数：{system.student_count()}")
    print()
    print("各科平均分：")
    for k, v in avg.items():
        print(f"  {k}：{v}")
    print()
    print("各科及格率：")
    for k, v in passed.items():
        print(f"  {k}：{v:.2f}%")
    print()
    print("总分排名（前 10 名）：")
    print("-" * 80)
    for i, stu in enumerate(rank[:10], 1):
        print(f"  第{i:>2}名  {stu.name:<6}  总分：{stu.total_score():>6.1f}  平均分：{stu.average_score():>5.2f}")
    print("-" * 80)


def make_excel(system: GradeSystem) -> None:
    print("\n--- 导出 Excel 表格 ---")
    df = system.m_excel()
    if df.empty:
        print("（暂无学生数据）")
        return

    filename = input("请输入导出文件名（直接回车默认为 grade_report.xlsx）：").strip()
    if not filename:
        filename = "grade_report.xlsx"
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    try:
        df.to_excel(filename, engine="openpyxl")
        print(f"Excel 表格已生成：{filename}")
        print("预览：")
        print(df)
    except ImportError:
        print("导出失败：缺少 openpyxl 库。请先运行: pip install openpyxl")
    except Exception as e:
        print(f"导出失败：{e}")


def do_chart(system: GradeSystem) -> None:
    print("\n--- 生成成绩分布图 ---")
    if system.student_count() == 0:
        print("（暂无学生数据）")
        return

    filename = input("请输入图片文件名（直接回车默认为 score_distribution.png）：").strip()
    if not filename:
        filename = "score_distribution.png"
    if not filename.endswith(".png"):
        filename += ".png"

    try:
        dist = system.make_chart(filename)
        if dist is None:
            print("（暂无学生数据）")
            return
        print(f"柱状图已生成：{filename}")
        print("区间分布：")
        for k, v in dist.items():
            print(f"  {k}：{int(v)} 人")
    except Exception as e:
        print(f"生成失败：{e}")





def main() -> None:
    system = GradeSystem(data_file="students.json")

    print(f"欢迎使用 {system.SYSTEM_NAME} v{system.SYSTEM_VERSION}")
    print(f"已加载 {system.student_count()} 名学生数据。")
    time.sleep(0.5)

    while True:
        show_menu(system)
        choice = input("请选择操作（1-10）：").strip()

        if choice == "1":
            do_add(system)
        elif choice == "2":
            do_update(system)
        elif choice == "3":
            do_delete(system)
        elif choice == "4":
            do_query(system)
        elif choice == "5":
            do_show_all(system)
        elif choice == "6":
            do_stats(system)
        elif choice == "7":
            make_excel(system)
        elif choice == "8":
            do_chart(system)
        elif choice == "9":
            system.save()
            print("数据已保存。")
        elif choice == "10":
            system.save()
            print("数据已保存，系统已退出。")
            break
        else:
            print("输入无效，请输入 1-10 之间的数字。")

        # 每次操作后自动保存，防止数据丢失
        if choice in ("1", "2", "3"):
            system.save()


if __name__ == "__main__":
    main()