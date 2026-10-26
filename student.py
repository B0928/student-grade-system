"""
学生数据模型类
只负责存数据和提供数据相关的方法，不做任何 input/print
遵循"职责分离"原则：数据层 = 数据 + 数据操作
"""


class Student:
    """学生类：封装单个学生的基本信息与成绩"""

    def __init__(self, name: str, chinese: float, math: float, english: float,
                 student_id=None) -> None:
        if not name.strip():
            raise ValueError("学生姓名不能为空")
        self._validate_score(chinese, "语文")
        self._validate_score(math, "数学")
        self._validate_score(english, "英语")

        self.name = name.strip()
        self.chinese = float(chinese)
        self.math = float(math)
        self.english = float(english)
        # 学号为唯一标识，允许同名；None 表示旧数据，由 GradeSystem 加载时补齐
        self.student_id = str(student_id).strip() if student_id is not None else None

    @staticmethod
    def _validate_score(score: float, subject: str) -> None:
        """校验成绩是否合法，不合法则抛出 ValueError"""
        try:
            score = float(score)
        except (TypeError, ValueError):
            raise ValueError(f"{subject}成绩必须是数字")
        if not 0 <= score <= 100:
            raise ValueError(f"{subject}成绩必须在 0-100 之间")

    def update_score(self, subject: str, score: float) -> None:
        """
        更新指定科目成绩
        subject: 'chinese' | 'math' | 'english' 或中文'语文'/'数学'/'英语'
        """
        subject_map = {
            "语文": "chinese",
            "数学": "math",
            "英语": "english",
            "chinese": "chinese",
            "math": "math",
            "english": "english",
        }
        key = subject_map.get(subject)
        if key is None:
            raise ValueError(f"未知科目：{subject}")

        self._validate_score(score, subject)
        setattr(self, key, float(score))

    def total_score(self) -> float:
        """返回总分"""
        return self.chinese + self.math + self.english

    def average_score(self) -> float:
        """返回平均分，保留 2 位小数"""
        return round(self.total_score() / 3, 2)

    def to_dict(self) -> dict:
        """转成字典，用于持久化"""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "chinese": self.chinese,
            "math": self.math,
            "english": self.english,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """从字典创建 Student 对象；旧数据没有学号字段时用 .get 兼容"""
        return cls(
            name=data["name"],
            chinese=data["chinese"],
            math=data["math"],
            english=data["english"],
            student_id=data.get("student_id"),
        )

    def __str__(self) -> str:
        return (
            f"学号：{self.student_id} | "
            f"姓名：{self.name} | "
            f"语文：{self.chinese} | "
            f"数学：{self.math} | "
            f"英语：{self.english} | "
            f"总分：{self.total_score()} | "
            f"平均分：{self.average_score()}"
        )
