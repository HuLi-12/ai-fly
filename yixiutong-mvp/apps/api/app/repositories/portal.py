from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.services.auth import PortalUser


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _to_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(raw: str | None, fallback: object) -> object:
    if not raw:
        return fallback
    return json.loads(raw)


class PortalRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_defaults()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_orders (
                    work_order_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    scene_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    applicant_id TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    applicant_role TEXT NOT NULL,
                    assignee_role TEXT NOT NULL,
                    assignee_name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    symptom_text TEXT NOT NULL,
                    provider_used TEXT NOT NULL,
                    latest_note TEXT NOT NULL,
                    final_resolution TEXT NOT NULL,
                    diagnosis_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    work_order_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approval_tasks (
                    approval_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    scene_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assignee_role TEXT NOT NULL,
                    assignee_name TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notification_channels (
                    channel TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    webhook_url TEXT NOT NULL DEFAULT '',
                    secret TEXT NOT NULL DEFAULT '',
                    receiver_hint TEXT NOT NULL DEFAULT '',
                    last_status TEXT NOT NULL DEFAULT '未验证',
                    last_message TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                """
            )

    def _seed_defaults(self) -> None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) AS count FROM notification_channels").fetchone()["count"]
            if count == 0:
                now = _now()
                conn.executemany(
                    """
                    INSERT INTO notification_channels(channel, display_name, enabled, webhook_url, secret, receiver_hint, last_status, last_message, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("wecom_bot", "企业微信群机器人", 0, "", "", "维修群 / 质量群", "未配置", "", now),
                        ("feishu_bot", "飞书自定义机器人", 0, "", "", "工艺协同群", "未配置", "", now),
                    ],
                )

            work_order_count = conn.execute("SELECT COUNT(*) AS count FROM work_orders").fetchone()["count"]
            if work_order_count > 0:
                return

            now = _now()
            demo_orders = [
                {
                    "work_order_id": "WO-DEMO-FAULT-001",
                    "request_id": "REQ-DEMO-FAULT-001",
                    "title": "总装工位 E-204 振动温升排故",
                    "scene_type": "fault_diagnosis",
                    "status": "待审批",
                    "approval_status": "待审批",
                    "priority": "高",
                    "risk_level": "high",
                    "applicant_id": "u-maint-01",
                    "applicant_name": "张伟",
                    "applicant_role": "maintenance_engineer",
                    "assignee_role": "maintenance_engineer",
                    "assignee_name": "维修工程师席位",
                    "summary": "夜班运行 6 小时后出现振动与温升叠加告警，需要人工复核后派工。",
                    "symptom_text": "设备运行时振动异常，并伴随温度持续升高。",
                    "provider_used": "ollama:fallback:yixiutong-qwen3b",
                    "latest_note": "已生成排故草案，等待审批主管确认是否允许停机检修。",
                    "final_resolution": "",
                    "diagnosis_json": _to_json(
                        {
                            "possible_causes": ["传动链磨损或轴承松旷导致振动放大。", "冷却回路衰减引发温升并诱发二次振动。", "温度传感器或告警链路存在漂移。"],
                            "recommended_checks": ["执行停机挂牌并复核联轴器、轴承和润滑状态。", "检查风扇、冷却回路与堵塞点。", "使用手持仪器交叉校验温度测点。"],
                            "recommended_actions": ["未经人工批准不得复机。", "按机械、冷却、传感三段顺序组织排故。", "完成检修后回填工单和点检记录。"],
                        }
                    ),
                    "evidence_json": _to_json(
                        [
                            {"source_type": "manual", "title": "E-204 排故手册", "snippet": "振动与温升同时出现时必须先停机并人工确认。", "score": 0.96},
                            {"source_type": "case", "title": "轴承松旷案例", "snippet": "历史案例显示轴承松旷与冷却受阻会叠加触发 E-204。", "score": 0.88},
                        ]
                    ),
                    "work_order_json": _to_json(
                        {
                            "summary": "E-204 排故工单草案",
                            "steps": ["停机挂牌", "检查轴承和联轴器", "检查冷却风道与风机", "交叉校验温度测点"],
                            "risk_notice": "高风险，需主管审批后派工。",
                            "assignee_placeholder": "维修工程师",
                        }
                    ),
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "work_order_id": "WO-DEMO-PROC-001",
                    "request_id": "REQ-DEMO-PROC-001",
                    "title": "热处理工序 PROC-118 偏差处置",
                    "scene_type": "process_deviation",
                    "status": "待签审",
                    "approval_status": "待审批",
                    "priority": "中",
                    "risk_level": "medium",
                    "applicant_id": "u-proc-01",
                    "applicant_name": "刘敏",
                    "applicant_role": "process_engineer",
                    "assignee_role": "process_engineer",
                    "assignee_name": "工艺工程师席位",
                    "summary": "热处理保温时间低于合格窗口，需要批次冻结与临时工艺处置。",
                    "symptom_text": "热处理保温时间偏低，批次参数出现漂移。",
                    "provider_used": "ollama:fallback:yixiutong-qwen3b",
                    "latest_note": "等待工艺签审，确认是否允许返工或补充热处理。",
                    "final_resolution": "",
                    "diagnosis_json": _to_json(
                        {
                            "possible_causes": ["热处理保温时间偏离合格窗口。", "工装更换后参数回填不完整。", "班组交接时未同步最新工艺卡。"],
                            "recommended_checks": ["比对当前参数与最近合格批次。", "复核工装校准记录。", "检查班组交接与工艺卡版本。"],
                            "recommended_actions": ["冻结受影响批次。", "形成临时工艺处置单。", "待工艺签审后执行返工或复验。"],
                        }
                    ),
                    "evidence_json": _to_json(
                        [
                            {"source_type": "manual", "title": "工艺偏差处置手册", "snippet": "出现保温时间偏低时，应先冻结批次并启动工艺签审。", "score": 0.93}
                        ]
                    ),
                    "work_order_json": _to_json(
                        {
                            "summary": "PROC-118 偏差处置单草案",
                            "steps": ["冻结批次", "复核参数记录", "形成临时工艺处置", "等待签审"],
                            "risk_notice": "中风险，需要工艺签审。",
                            "assignee_placeholder": "工艺工程师",
                        }
                    ),
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "work_order_id": "WO-DEMO-QUAL-001",
                    "request_id": "REQ-DEMO-QUAL-001",
                    "title": "终检 QA-305 表面缺陷隔离处置",
                    "scene_type": "quality_inspection",
                    "status": "待隔离",
                    "approval_status": "待审批",
                    "priority": "高",
                    "risk_level": "high",
                    "applicant_id": "u-quality-01",
                    "applicant_name": "王钰",
                    "applicant_role": "quality_engineer",
                    "assignee_role": "quality_engineer",
                    "assignee_name": "质量工程师席位",
                    "summary": "终检发现划伤与毛刺，需要隔离批次并准备 MRB 处置。",
                    "symptom_text": "终检发现表面划伤与边缘毛刺。",
                    "provider_used": "ollama:fallback:yixiutong-qwen3b",
                    "latest_note": "等待质量工程师确认隔离范围与 MRB 升级。", 
                    "final_resolution": "",
                    "diagnosis_json": _to_json(
                        {
                            "possible_causes": ["搬运过程造成表面损伤。", "去毛刺工序控制不稳定。", "量具或检验方法存在漂移。"],
                            "recommended_checks": ["复核同批次零件和工位。", "检查去毛刺与搬运记录。", "确认量具与检验标准版本。"],
                            "recommended_actions": ["隔离批次。", "停止后续放行。", "整理缺陷证据并提交 MRB。"],
                        }
                    ),
                    "evidence_json": _to_json(
                        [
                            {"source_type": "case", "title": "终检缺陷案例", "snippet": "表面划伤与毛刺并发时应优先隔离批次，禁止继续放行。", "score": 0.95}
                        ]
                    ),
                    "work_order_json": _to_json(
                        {
                            "summary": "QA-305 质量隔离单草案",
                            "steps": ["隔离批次", "复检同批次零件", "整理缺陷照片与尺寸记录", "提交 MRB"],
                            "risk_notice": "高风险，需质量审批后继续流转。",
                            "assignee_placeholder": "质量工程师",
                        }
                    ),
                    "created_at": now,
                    "updated_at": now,
                },
            ]

            conn.executemany(
                """
                INSERT INTO work_orders(
                    work_order_id, request_id, title, scene_type, status, approval_status, priority, risk_level,
                    applicant_id, applicant_name, applicant_role, assignee_role, assignee_name, summary, symptom_text,
                    provider_used, latest_note, final_resolution, diagnosis_json, evidence_json, work_order_json,
                    created_at, updated_at
                )
                VALUES(
                    :work_order_id, :request_id, :title, :scene_type, :status, :approval_status, :priority, :risk_level,
                    :applicant_id, :applicant_name, :applicant_role, :assignee_role, :assignee_name, :summary, :symptom_text,
                    :provider_used, :latest_note, :final_resolution, :diagnosis_json, :evidence_json, :work_order_json,
                    :created_at, :updated_at
                )
                """,
                demo_orders,
            )

            conn.executemany(
                """
                INSERT INTO approval_tasks(
                    approval_id, work_order_id, title, scene_type, status, assignee_role, assignee_name, priority, comment, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("AP-DEMO-FAULT-001", "WO-DEMO-FAULT-001", "E-204 停机检修审批", "fault_diagnosis", "pending", "supervisor", "陈浩", "高", "等待主管确认是否允许停机检修。", now, now),
                    ("AP-DEMO-PROC-001", "WO-DEMO-PROC-001", "PROC-118 工艺签审", "process_deviation", "pending", "process_engineer", "刘敏", "中", "等待工艺签审。", now, now),
                    ("AP-DEMO-QUAL-001", "WO-DEMO-QUAL-001", "QA-305 质量隔离审批", "quality_inspection", "pending", "quality_engineer", "王钰", "高", "等待质量工程师确认隔离范围。", now, now),
                ],
            )

    def _scene_display(self, scene_type: str) -> str:
        return {
            "fault_diagnosis": "智能排故",
            "process_deviation": "工艺偏差",
            "quality_inspection": "质量处置",
        }.get(scene_type, "综合场景")

    def _scene_assignee_role(self, scene_type: str) -> str:
        return {
            "fault_diagnosis": "maintenance_engineer",
            "process_deviation": "process_engineer",
            "quality_inspection": "quality_engineer",
        }.get(scene_type, "maintenance_engineer")

    def _scene_assignee_name(self, scene_type: str) -> str:
        return {
            "fault_diagnosis": "维修工程师席位",
            "process_deviation": "工艺工程师席位",
            "quality_inspection": "质量工程师席位",
        }.get(scene_type, "业务席位")

    def _approval_role(self, scene_type: str, risk_level: str) -> str:
        if risk_level == "high":
            return "supervisor" if scene_type == "fault_diagnosis" else self._scene_assignee_role(scene_type)
        return self._scene_assignee_role(scene_type)

    def _approval_name(self, role: str) -> str:
        return {
            "maintenance_engineer": "张伟",
            "process_engineer": "刘敏",
            "quality_engineer": "王钰",
            "supervisor": "陈浩",
            "admin": "系统管理员",
        }.get(role, "待分配")

    def _priority_label(self, risk_level: str) -> str:
        return {"high": "高", "medium": "中", "low": "低"}.get(risk_level, "中")

    def _approval_status_label(self, status: str) -> str:
        return {
            "pending": "待审批",
            "approved": "已通过",
            "rejected": "已驳回",
        }.get(status, status)

    def _work_order_status_bucket(self, status: str, approval_status: str, final_resolution: str) -> tuple[str, str]:
        if final_resolution or status == "已完成":
            return "completed", "已完成"
        if status == "驳回重审" or approval_status == "已驳回":
            return "rework", "驳回重审"
        if status == "待审批" or approval_status == "待审批":
            return "pending_approval", "待审批"
        if status in {"待执行", "待签审", "待隔离"}:
            return "pending_execution", "待执行"
        if status in {"处理中", "执行中", "排故中"}:
            return "in_progress", "处理中"
        return "pending_execution", "待执行"

    def _can_view_scene(self, user: PortalUser, scene_type: str) -> bool:
        if user.role in {"admin", "supervisor"}:
            return True
        if user.role == "maintenance_engineer":
            return scene_type == "fault_diagnosis"
        if user.role == "process_engineer":
            return scene_type == "process_deviation"
        if user.role == "quality_engineer":
            return scene_type == "quality_inspection"
        return False

    def _row_to_work_order(self, row: sqlite3.Row) -> dict:
        status_bucket, status_bucket_label = self._work_order_status_bucket(
            row["status"],
            row["approval_status"],
            row["final_resolution"],
        )
        return {
            "work_order_id": row["work_order_id"],
            "request_id": row["request_id"],
            "title": row["title"],
            "scene_type": row["scene_type"],
            "scene_label": self._scene_display(row["scene_type"]),
            "status": row["status"],
            "approval_status": row["approval_status"],
            "status_bucket": status_bucket,
            "status_bucket_label": status_bucket_label,
            "priority": row["priority"],
            "risk_level": row["risk_level"],
            "applicant_name": row["applicant_name"],
            "applicant_role": row["applicant_role"],
            "assignee_role": row["assignee_role"],
            "assignee_name": row["assignee_name"],
            "summary": row["summary"],
            "symptom_text": row["symptom_text"],
            "provider_used": row["provider_used"],
            "latest_note": row["latest_note"],
            "final_resolution": row["final_resolution"],
            "diagnosis": _from_json(row["diagnosis_json"], {}),
            "evidence": _from_json(row["evidence_json"], []),
            "work_order_draft": _from_json(row["work_order_json"], {}),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_approval(self, row: sqlite3.Row) -> dict:
        return {
            "approval_id": row["approval_id"],
            "work_order_id": row["work_order_id"],
            "title": row["title"],
            "scene_type": row["scene_type"],
            "scene_label": self._scene_display(row["scene_type"]),
            "status": row["status"],
            "status_label": self._approval_status_label(row["status"]),
            "assignee_role": row["assignee_role"],
            "assignee_name": row["assignee_name"],
            "priority": row["priority"],
            "comment": row["comment"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def create_work_order_from_diagnosis(
        self,
        request_payload: dict,
        diagnosis_response: dict,
        user: PortalUser | None,
    ) -> dict:
        now = _now()
        scene_type = diagnosis_response["scene_type"]
        request_id = diagnosis_response["request_id"]
        work_order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        priority = self._priority_label(diagnosis_response["risk_level"])
        applicant_id = user.user_id if user else "u-demo-guest"
        applicant_name = user.display_name if user else "演示发起人"
        applicant_role = user.role if user else "guest"
        assignee_role = self._scene_assignee_role(scene_type)
        assignee_name = self._scene_assignee_name(scene_type)
        approval_role = self._approval_role(scene_type, diagnosis_response["risk_level"])
        approval_status = "待审批" if diagnosis_response["requires_human_confirmation"] else "无需审批"
        status = "待审批" if diagnosis_response["requires_human_confirmation"] else "待执行"
        title = f"{self._scene_display(scene_type)} | {request_payload['fault_code']}"
        summary = diagnosis_response["work_order_draft"]["summary"]
        latest_note = f"{applicant_name} 发起了 Agent 分析，等待进入下一步流程。"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO work_orders(
                    work_order_id, request_id, title, scene_type, status, approval_status, priority, risk_level,
                    applicant_id, applicant_name, applicant_role, assignee_role, assignee_name, summary, symptom_text,
                    provider_used, latest_note, final_resolution, diagnosis_json, evidence_json, work_order_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    work_order_id,
                    request_id,
                    title,
                    scene_type,
                    status,
                    approval_status,
                    priority,
                    diagnosis_response["risk_level"],
                    applicant_id,
                    applicant_name,
                    applicant_role,
                    assignee_role,
                    assignee_name,
                    summary,
                    request_payload["symptom_text"],
                    diagnosis_response["provider_used"],
                    latest_note,
                    "",
                    _to_json(diagnosis_response["diagnosis"]),
                    _to_json(diagnosis_response["evidence"]),
                    _to_json(diagnosis_response["work_order_draft"]),
                    now,
                    now,
                ),
            )
            if diagnosis_response["requires_human_confirmation"]:
                conn.execute(
                    """
                    INSERT INTO approval_tasks(
                        approval_id, work_order_id, title, scene_type, status, assignee_role, assignee_name, priority, comment, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"AP-{uuid4().hex[:8].upper()}",
                        work_order_id,
                        f"{title} 审批",
                        scene_type,
                        "pending",
                        approval_role,
                        self._approval_name(approval_role),
                        priority,
                        "等待审批处理。",
                        now,
                        now,
                    ),
                )

        return self.get_work_order_detail(work_order_id)

    def list_work_orders(
        self,
        user: PortalUser,
        scene_type: str | None = None,
        keyword: str | None = None,
        status_bucket: str | None = None,
    ) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM work_orders ORDER BY updated_at DESC").fetchall()
        items = [self._row_to_work_order(row) for row in rows if self._can_view_scene(user, row["scene_type"])]
        if scene_type:
            items = [item for item in items if item["scene_type"] == scene_type]
        if status_bucket and status_bucket != "all":
            items = [item for item in items if item["status_bucket"] == status_bucket]
        if keyword:
            lowered = keyword.lower()
            items = [item for item in items if lowered in item["title"].lower() or lowered in item["summary"].lower() or lowered in item["symptom_text"].lower()]
        return items

    def get_work_order_detail(self, work_order_id: str) -> dict:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM work_orders WHERE work_order_id = ?", (work_order_id,)).fetchone()
            if row is None:
                raise KeyError(work_order_id)
            work_order = self._row_to_work_order(row)
            approvals = conn.execute(
                "SELECT * FROM approval_tasks WHERE work_order_id = ? ORDER BY created_at DESC",
                (work_order_id,),
            ).fetchall()
        work_order["approvals"] = [self._row_to_approval(item) for item in approvals]
        return work_order

    def get_work_order_by_request(self, request_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT work_order_id FROM work_orders WHERE request_id = ?", (request_id,)).fetchone()
        if row is None:
            return None
        return self.get_work_order_detail(row["work_order_id"])

    def list_approval_tasks(self, user: PortalUser, include_history: bool = False, status: str | None = None) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM approval_tasks ORDER BY updated_at DESC").fetchall()
        items = [self._row_to_approval(row) for row in rows]
        if user.role in {"admin", "supervisor"}:
            visible = items
        else:
            visible = [item for item in items if item["assignee_role"] == user.role]
        if status:
            visible = [item for item in visible if item["status"] == status]
        elif not include_history:
            visible = [item for item in visible if item["status"] == "pending"]
        return visible

    def get_dashboard_summary(self, user: PortalUser) -> dict:
        work_orders = self.list_work_orders(user)
        approvals = self.list_approval_tasks(user)
        pending_approvals = [item for item in approvals if item["status"] == "pending"]
        pending_execution = [item for item in work_orders if item["status_bucket"] == "pending_execution"]
        in_progress = [item for item in work_orders if item["status_bucket"] == "in_progress"]
        done = [item for item in work_orders if item["status_bucket"] == "completed"]
        rework = [item for item in work_orders if item["status_bucket"] == "rework"]
        return {
            "work_order_count": len(work_orders),
            "pending_approval_count": len(pending_approvals),
            "pending_execution_count": len(pending_execution),
            "in_progress_count": len(in_progress),
            "completed_count": len(done),
            "rework_count": len(rework),
        }

    def decide_work_order(self, work_order_id: str, approved: bool, comment: str, edited_actions: list[str], reviewer: PortalUser | None) -> dict:
        now = _now()
        work_order = self.get_work_order_detail(work_order_id)
        diagnosis = work_order["diagnosis"]
        if edited_actions:
            diagnosis["recommended_actions"] = edited_actions
            work_order_draft = work_order["work_order_draft"]
            work_order_draft["steps"] = work_order_draft.get("steps", [])
            work_order_draft["steps"] = edited_actions[: len(work_order_draft["steps"]) or len(edited_actions)]
        else:
            work_order_draft = work_order["work_order_draft"]
        reviewer_name = reviewer.display_name if reviewer else "人工复核"
        status = "待执行" if approved else "驳回重审"
        approval_status = "已通过" if approved else "已驳回"
        note = f"{reviewer_name} {'通过' if approved else '驳回'}了审批。"
        if comment:
            note += f" 备注：{comment}"

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE work_orders
                SET status = ?, approval_status = ?, latest_note = ?, diagnosis_json = ?, work_order_json = ?, updated_at = ?
                WHERE work_order_id = ?
                """,
                (
                    status,
                    approval_status,
                    note,
                    _to_json(diagnosis),
                    _to_json(work_order_draft),
                    now,
                    work_order_id,
                ),
            )
            conn.execute(
                """
                UPDATE approval_tasks
                SET status = ?, comment = ?, updated_at = ?
                WHERE work_order_id = ? AND status = 'pending'
                """,
                (
                    "approved" if approved else "rejected",
                    note,
                    now,
                    work_order_id,
                ),
            )
        return self.get_work_order_detail(work_order_id)

    def save_feedback(self, work_order_id: str, feedback_text: str, final_resolution: str, operator: PortalUser | None) -> dict:
        work_order = self.get_work_order_detail(work_order_id)
        now = _now()
        operator_name = operator.display_name if operator else "业务人员"
        if final_resolution:
            status = "已完成"
            approval_status = "已闭环"
        elif work_order["status"] in {"待执行", "待签审", "待隔离"}:
            status = "处理中"
            approval_status = work_order["approval_status"]
        else:
            status = work_order["status"]
            approval_status = work_order["approval_status"]
        note = f"{operator_name} 回填了反馈。"
        if feedback_text:
            note += f" 反馈：{feedback_text}"

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE work_orders
                SET status = ?, approval_status = ?, final_resolution = ?, latest_note = ?, updated_at = ?
                WHERE work_order_id = ?
                """,
                (
                    status,
                    approval_status,
                    final_resolution or work_order["final_resolution"],
                    note,
                    now,
                    work_order_id,
                ),
            )
        return self.get_work_order_detail(work_order_id)

    def list_notification_channels(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM notification_channels ORDER BY channel").fetchall()
        return [dict(row) for row in rows]

    def update_notification_channel(self, channel: str, enabled: bool, webhook_url: str, secret: str, receiver_hint: str) -> dict:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE notification_channels
                SET enabled = ?, webhook_url = ?, secret = ?, receiver_hint = ?, updated_at = ?
                WHERE channel = ?
                """,
                (1 if enabled else 0, webhook_url, secret, receiver_hint, now, channel),
            )
        return self.get_notification_channel(channel)

    def get_notification_channel(self, channel: str) -> dict:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM notification_channels WHERE channel = ?", (channel,)).fetchone()
        if row is None:
            raise KeyError(channel)
        return dict(row)

    def record_notification_result(self, channel: str, status_text: str, message: str) -> dict:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE notification_channels SET last_status = ?, last_message = ?, updated_at = ? WHERE channel = ?",
                (status_text, message, now, channel),
            )
        return self.get_notification_channel(channel)
