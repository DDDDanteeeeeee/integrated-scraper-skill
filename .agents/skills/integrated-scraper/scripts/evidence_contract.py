"""Offline evidence integrity checks, not a claim of factual truth or completeness."""
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit


def timestamp(value):
    try:
        return isinstance(value, str) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def assessments(rows, criteria, valid_ids):
    if not isinstance(rows, list) or len(rows) != len(criteria):
        return ["验收必须逐条对应标准"]
    errors = []
    if [r.get("criterion") if isinstance(r, dict) else None for r in rows] != criteria:
        errors.append("验收标准与任务不一致")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("验收记录必须是对象")
            continue
        refs = row.get("evidence_ids")
        if row.get("passed") is not True or not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errors.append("验收缺少通过理由")
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or ref not in valid_ids for ref in refs):
            errors.append("验收未关联有效证据")
    return errors


def validate_evidence(result, run_dir, criteria, status):
    errors = []
    rows = result.get("evidence")
    if not isinstance(rows, list) or not rows:
        return ["缺少原始证据清单 evidence"]
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("证据必须是对象")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            errors.append("证据 ID 无效或重复")
            continue
        ids.add(identifier)
        try:
            url = urlsplit(row.get("url", ""))
            if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
                raise ValueError("来源 URL 无效或包含凭据")
            if not timestamp(row.get("captured_at")):
                raise ValueError("采集时间必须包含时区")
            relative = row.get("path")
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
                raise ValueError("证据路径必须相对任务目录")
            path = (run_dir / relative).resolve()
            if not path.is_relative_to(run_dir.resolve()):
                raise ValueError("证据路径越出任务目录")
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("原始证据文件缺失或为空")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if row.get("sha256") != digest:
                raise ValueError("原始证据哈希不一致")
        except (OSError, ValueError, TypeError) as error:
            errors.append(f"{identifier}: {error}")
    if status == "success" and (type(result.get("evidence_count")) is not int or result["evidence_count"] != len(rows)):
        errors.append("evidence_count 必须等于证据清单长度")
    if status == "empty_verified":
        empty = result.get("empty_evidence")
        if result.get("empty_verified") is not True or not isinstance(empty, list) or not empty or any(not isinstance(ref, str) or ref not in ids for ref in empty):
            errors.append("零结果必须关联原始证据 ID")
    if "collection_check" in result:
        try:
            ref = result["collection_check"]["evidence_id"]
            row = next(row for row in rows if row.get("id") == ref)
            path = (run_dir / row["path"]).resolve()
            if not path.is_relative_to(run_dir.resolve()):
                raise ValueError("collection check path escaped run")
            spec = importlib.util.spec_from_file_location("collection_quality", Path(__file__).with_name("collection_quality.py"))
            quality = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(quality)
            check = quality.audit_comments(json.loads(path.read_text(encoding="utf-8-sig")))
            if not check["ok"] or (status == "empty_verified" and not check["zero_verified"]):
                errors.append("评论完整度未通过：" + ",".join(check["issues"]))
        except (OSError, ValueError, TypeError, KeyError, StopIteration) as error:
            errors.append(f"collection_check 无效：{error}")
    errors.extend(assessments(result.get("assessments"), criteria, ids))
    return errors
