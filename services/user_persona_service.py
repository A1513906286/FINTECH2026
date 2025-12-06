"""
用户画像服务
-----------------
基于 user_persona 目录下由 PDFService 导出的银行流水 txt，
调用本地 Ollama 大模型，抽取用户消费习惯画像，并生成 *_processed.json。

依赖：
- 本地已安装并启动 Ollama: 例如 `ollama serve`
- 已拉取模型: 例如 `ollama pull llama3.2:3b`
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests


class UserPersonaService:
    """负责从银行流水 txt 构建用户消费画像，并在本地缓存/读取。"""

    def __init__(
        self,
        user_persona_folder: str = "user_persona",
        model_name: str = "llama3.2:3b",
        ollama_url: str = "http://127.0.0.1:11434",
    ):
        self.user_persona_folder = user_persona_folder
        self.model_name = model_name
        self.ollama_url = ollama_url.rstrip("/")
        os.makedirs(self.user_persona_folder, exist_ok=True)

    # ==================== 对外主流程 ====================

    def build_persona_for_all(self) -> List[str]:
        """
        为 user_persona 目录下所有尚未处理的 txt 构建画像。
        返回已生成的 persona 文件路径列表。
        """
        generated_files: List[str] = []

        for filename in os.listdir(self.user_persona_folder):
            if not filename.lower().endswith(".txt"):
                continue
            if filename.endswith("_processed.txt") or filename.endswith("_processed.json"):
                continue

            txt_path = os.path.join(self.user_persona_folder, filename)
            persona_path = self._get_persona_path(txt_path)

            if os.path.exists(persona_path):
                # 已有画像文件，跳过
                continue

            persona = self.build_persona_from_txt(txt_path)
            if persona:
                self._save_persona(persona_path, persona)
                generated_files.append(persona_path)

        return generated_files

    def build_persona_from_txt(self, txt_path: str) -> Optional[Dict[str, Any]]:
        """
        从单个 txt 文件构建用户画像（只依赖银行流水与统计信息，获得大类偏好）。
        返回 persona dict，如果调用失败则返回 None。
        """
        if not os.path.exists(txt_path):
            print(f"[UserPersona] 文件不存在: {txt_path}")
            return None

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[UserPersona] 读取文件失败 {txt_path}: {e}")
            return None

        # 为避免请求体过大，只取前若干行（重点包含统计信息 + 一部分交易样本）
        lines = content.splitlines()
        head_part = "\n".join(lines[:260])  # 统计信息 + 若干交易样本，基本足够推断大类

        system_prompt = (
            "你是银行风控和消费行为分析专家，现在要根据中国用户的银行流水和统计信息，"
            "推断该用户的【消费习惯与偏好画像】。\n"
            "注意：\n"
            "1. 流水中出现的平台/商户名（如 美团、支付宝、财付通、茶百道、奶茶、咖啡、网鱼网咖、肯德基 等）"
            "只用来推断【大类偏好】，不要做细粒度、无根据的臆测；\n"
            "2. 如果证据不足，就回答“未知”或“无法判断”，不要假设；\n"
            "3. 要特别关注：是否高频小额消费、夜间消费、网购/外卖/线下餐饮、娱乐(网吧/游戏)、出行(地铁/打车/共享单车)、"
            "生活超市/便利店等。\n"
            "4. 输出时请使用简体中文描述，但 JSON 字段名使用英文。"
        )

        user_prompt = f"""
下面是某个用户的银行流水统计信息和部分交易明细，请基于这些信息，推断该用户的消费习惯（只能做“类别层面”的画像，不要编造具体品牌故事）：

================= 银行流水文本开始 =================
{head_part}
================= 银行流水文本结束 =================

请严格按照下面的 JSON 模板输出（不要输出任何多余文字），其中字符串内容用简体中文：
{{
  "user_name": "<如果能从文本中识别到户名就填，否则填 空>",
  "summary": "用1-2句话概括该用户的总体消费特征，例如：高频小额餐饮+奶茶，偶尔大额教育/医疗支出 等。",
  "income_stability": "高/中/低/未知",
  "risk_preference": "偏稳健/中性/偏激进/未知",
  "consumption_patterns": {{
    "main_categories": ["餐饮与外卖", "咖啡奶茶", "日常通勤与地铁", "网购/平台支付", "娱乐(网吧/游戏)", "医疗健康", "转账与理财操作" 等，只保留有证据的项],
    "small_ticket_high_frequency": true,
    "night_consumption_tendency": "明显/一般/不明显/未知",
    "online_offline_mix": "偏线上/线上线下均衡/偏线下/未知"
  }},
  "preferred_tags": [
    "coffee",          // 如果从流水看出明显咖啡/奶茶偏好
    "milk_tea",
    "fast_food",
    "convenience_store",
    "online_shopping",
    "digital_payment",
    "gaming_internet_cafe",
    "public_transport",
    "travel",
    "healthcare",
    "unknown"          // 若证据不足，可以只给 ["unknown"]
  ],
  "evidence_examples": [
    "用1句话概括一类证据，例如：频繁出现 茶百道/喜茶/奶茶 相关消费，金额 10-30 元",
    "再给 2-4 条类似的证据说明即可。"
  ]
}}
"""

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 800,
            },
        }

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"[UserPersona] 调用 Ollama 失败: {e}")
            return None

        # 解析 JSON（只保留第一个 JSON 块）
        try:
            persona = self._extract_json_from_response(content)
            if isinstance(persona, dict):
                persona["source_txt"] = os.path.basename(txt_path)
                persona["generated_at"] = datetime.now().isoformat()
                return persona
        except Exception as e:
            print(f"[UserPersona] 解析 Ollama 响应失败: {e}")

        return None

    def get_latest_persona(self) -> Optional[Dict[str, Any]]:
        """
        获取 user_persona 目录下最新生成的 *_processed.json 画像，
        作为当前系统默认用户画像（示例项目中用于所有用户）。
        """
        json_files = []
        for filename in os.listdir(self.user_persona_folder):
            if filename.endswith("_processed.json"):
                full_path = os.path.join(self.user_persona_folder, filename)
                json_files.append((full_path, os.path.getmtime(full_path)))

        if not json_files:
            return None

        # 按修改时间排序，取最新
        json_files.sort(key=lambda x: x[1], reverse=True)
        latest_path = json_files[0][0]

        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[UserPersona] 读取画像失败 {latest_path}: {e}")
            return None

    # ==================== 内部工具函数 ====================

    def _get_persona_path(self, txt_path: str) -> str:
        """根据原始 txt 路径生成画像 json 路径。"""
        base = os.path.basename(txt_path)
        name, _ = os.path.splitext(base)
        persona_filename = f"{name}_processed.json"
        return os.path.join(self.user_persona_folder, persona_filename)

    def _save_persona(self, persona_path: str, persona: Dict[str, Any]) -> None:
        """保存画像到 JSON 文件。"""
        try:
            with open(persona_path, "w", encoding="utf-8") as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            print(f"[UserPersona] 用户画像已保存: {persona_path}")
        except Exception as e:
            print(f"[UserPersona] 保存画像失败 {persona_path}: {e}")

    def _extract_json_from_response(self, text: str) -> Any:
        """
        从大模型输出中提取 JSON（容错处理：允许前后有说明文字）。
        """
        text = text.strip()
        # 尝试直接 load
        try:
            return json.loads(text)
        except Exception:
            pass

        # 从第一个 '{' 到最后一个 '}' 截取
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
        # 如果还是失败，抛异常给上层
        raise ValueError("无法从响应中提取有效 JSON")


if __name__ == "__main__":
    """
    简单命令行测试：
    python -m services.user_persona_service
    """
    service = UserPersonaService()
    generated = service.build_persona_for_all()
    print("生成的画像文件:", generated)


