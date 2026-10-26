
import json
import os
from typing import List, Optional, Dict
from student import Student
import numpy as np
import pandas as pd
import matplotlib
# 默认用无界面后端 Agg（只保存图片、不弹窗）；以后要做交互窗口再临时切 TkAgg
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 让图表能正常显示中文（Windows 自带黑体），并修正负号显示
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

class GradeSystem:
    """教务管理系统：管理一批学生的成绩"""

    SYSTEM_NAME = "教务管理系统"
    SYSTEM_VERSION = "2.0"

    def __init__(self, data_file: str = "students.json"):
        self.students: List[Student] = []
        self._data_file = data_file
        self.load()  # 启动时自动加载数据

    # ---------- 增 ----------
    def add_student(self, name: str, chinese: float, math: float, english: float,
                    student_id=None) -> bool:
        """
        添加学生。学号重复返回 False，成功返回 True。
        student_id 为空时自动生成（S0001、S0002……）。允许同名，靠学号区分。
        成绩不合法会抛出 ValueError，由调用方处理。
        """
        if student_id is None or not str(student_id).strip():
            student_id = self._next_student_id()
        else:
            student_id = str(student_id).strip()
            if self.find_by_id(student_id) is not None:
                return False  # 学号已存在
        stu = Student(name, chinese, math, english, student_id=student_id)
        self.students.append(stu)
        return True

    def _next_student_id(self) -> str:
        """生成下一个学号：取现有 S 开头学号的最大编号 +1"""
        max_num = 0
        for stu in self.students:
            sid = str(getattr(stu, "student_id", "") or "")
            if sid.startswith("S") and sid[1:].isdigit():
                max_num = max(max_num, int(sid[1:]))
        return f"S{max_num + 1:04d}"

    # ---------- 删 ----------
    def delete_student(self, name: str) -> bool:
        """按姓名删除学生，找到并删除返回 True，没找到返回 False"""
        stu = self.find_student(name)
        if stu is None:
            return False
        else:
            self.students.remove(stu)
            return True

    # ---------- 改 ----------
    def update_student_score(self, name: str, subject: str, score: float) -> bool:
        """
        修改指定学生某科成绩
        找到并修改返回 True，没找到返回 False
        成绩不合法会抛出 ValueError
        """
        stu = self.find_student(name)
        if stu is None:
            return False
        else:
            stu.update_score(subject, score)
            return True

    # ---------- 查 ----------
    def find_student(self, name: str) -> Optional[Student]:
        """按姓名查找第一个匹配的学生（重名时建议用 find_all_by_name 或 find_by_id）"""
        for stu in self.students:
            if stu.name == name.strip():
                return stu
        return None

    def find_by_id(self, student_id: str) -> Optional[Student]:
        """按学号精确查找学生"""
        sid = str(student_id).strip()
        for stu in self.students:
            if stu.student_id == sid:
                return stu
        return None

    def find_all_by_name(self, name: str) -> List[Student]:
        """按姓名查找所有同名学生"""
        key = name.strip()
        return [stu for stu in self.students if stu.name == key]

    def delete_student_by_id(self, student_id: str) -> bool:
        """按学号删除学生"""
        stu = self.find_by_id(student_id)
        if stu is None:
            return False
        self.students.remove(stu)
        return True

    def get_all_students(self) -> List[Student]:
        """返回所有学生列表的副本（避免外部直接修改内部列表）"""
        return list(self.students)

    def student_count(self) -> int:
        return len(self.students)

    # ---------- 统计 ----------
    def class_average(self) -> Dict[str, float]:
        """
        计算全班各科平均分和总平均分
        返回字典：{'语文': xx, '数学': xx, '英语': xx, '总平均': xx}
        """
        if not self.students:
            return {"语文": 0.0, "数学": 0.0, "英语": 0.0, "总平均": 0.0}
        else:
            n = len(self.students)
            chinese_avg = sum(s.chinese for s in self.students) / n
            math_avg = sum(s.math for s in self.students) / n
            english_avg = sum(s.english for s in self.students) / n
            total_avg = sum(s.average_score() for s in self.students) / n

            return {
            "语文": round(chinese_avg, 2),
            "数学": round(math_avg, 2),
            "英语": round(english_avg, 2),
            "总平均": round(total_avg, 2),
            }

    def pass_rate(self) -> Dict[str, float]:
        """各科及格率，返回 0-100 的数值（如 85.0），是否格式化成百分号字符串由调用方决定"""
        if not self.students:
            return {"语文": 0.0, "数学": 0.0, "英语": 0.0}

        n = len(self.students)
        result = {}
        for subject, attr in [("语文", "chinese"), ("数学", "math"), ("英语", "english")]:
            passed = sum(1 for s in self.students if getattr(s, attr) >= 60)
            result[subject] = round(passed / n * 100, 2)
        return result

    def rank_by_total(self) -> List[Student]:
        """按总分从高到低排序，返回排序后的学生列表"""
        return sorted(self.students, key=lambda s: s.total_score(), reverse=True)

    # ---------- 持久化（JSON） ----------
    def save(self) -> None:
        """把学生列表保存到 JSON 文件"""
        data = [stu.to_dict() for stu in self.students]
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """从 JSON 文件加载学生数据。文件不存在则创建空文件；读取失败时提示并备份原文件，不静默覆盖。"""
        if not os.path.exists(self._data_file):
            self.save()
            return
        try:
            with open(self._data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.students = [Student.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 不静默清空：打印原因并把损坏文件改名备份，防止后续 save 把原数据覆盖
            backup = self._data_file + ".bak"
            try:
                os.replace(self._data_file, backup)
                print(f"警告：数据文件 {self._data_file} 读取失败（{e}），"
                      f"原文件已备份为 {backup}，本次以空数据启动。")
            except OSError:
                print(f"警告：数据文件 {self._data_file} 读取失败（{e}），"
                      f"且备份失败，本次以空数据启动（原文件未改动，退出时请不要保存）。")
            self.students = []
        # 兼容旧数据：没有学号的学生自动补一个
        for stu in self.students:
            if not getattr(stu, "student_id", None):
                stu.student_id = self._next_student_id()

    # ---------- 生成表格 ----------
    def m_excel(self):
        """构造一个按总分从高到低排序的 DataFrame，空数据返回空 DataFrame"""
        columns = ["学号", "姓名", "语文", "数学", "英语", "总分"]
        if not self.students:
            return pd.DataFrame(columns=columns).set_index("姓名")

        data_list = [
            {
                "学号": stu.student_id,
                "姓名": stu.name,
                "语文": stu.chinese,
                "数学": stu.math,
                "英语": stu.english,
                "总分": stu.total_score(),
            }
            for stu in self.students
        ]
        df = pd.DataFrame(data_list, columns=columns)
        df = df.sort_values("总分", ascending=False)
        df = df.set_index("姓名")
        return df

    # ---------- 生成成绩分布图 ----------
    def make_chart(self, filename: str = "score_distribution.png"):
        """
        把学生按总分分成三个区间，画柱状图并保存为 PNG。
        区间：低 < 200、中 200-249、高 ≥ 250
        成功返回区间分布字典，空数据返回 None。
        """
        if not self.students:
            return None

        labels = ["低 (<200)", "中 (200-249)", "高 (≥250)"]
        df = pd.DataFrame(
            [{"姓名": stu.name, "总分": stu.total_score()} for stu in self.students]
        )
        df["区间"] = pd.cut(
            df["总分"],
            bins=[0, 200, 250, 300],
            labels=labels,
            right=False,
            include_lowest=True,
        )

        # reindex 补齐三个区间（缺的补 0），避免柱子数量与 x 轴标签数量不一致
        dist = df["区间"].value_counts().reindex(labels, fill_value=0)

        # 全局已是 Agg 后端，直接画图保存，不弹窗
        plt.figure(figsize=(10, 5))
        plt.bar(dist.index, dist.values, label="学生成绩区间分布",
                color="black", width=0.5)
        plt.title("学生成绩区间分布", color="red", fontsize=20)
        plt.xlabel("总分区间", color="blue", fontsize=10)
        plt.ylabel("人数", color="blue", fontsize=10)
        plt.legend(loc="upper right", fontsize=10)
        plt.grid(axis="y", alpha=0.3, color="red", linestyle="--")
        plt.xticks(rotation=0, fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        # y 轴上限按实际人数动态留白，避免人数很少时柱子在顶部贴边
        plt.ylim(0, max(int(dist.max()) + 1, 3))
        # 柱子上标人数：x 用区间标签，y 用该区间人数
        for x, y in zip(dist.index, dist.values):
            plt.text(x, y, str(int(y)), fontsize=10, ha="center", va="bottom")
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()

        return dist.to_dict()
