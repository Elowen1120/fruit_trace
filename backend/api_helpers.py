"""统一 API 响应与业务辅助函数。"""
import re
from typing import Optional

from flask import jsonify

from models import PlantingData, ProductInfo, StorageData, TransportData


def api_ok(data=None, message="success"):
    return jsonify({"code": 200, "message": message, "data": data})


def api_err(code: int, message: str, http_status: Optional[int] = None):
    if http_status is None:
        if code == 401:
            http_status = 401
        elif code == 404:
            http_status = 404
        else:
            http_status = 400
    return jsonify({"code": code, "message": message, "data": None}), http_status


_P_ID = re.compile(r"^P(\d{3})$", re.I)
_RFID_FMT = re.compile(r"^RFID(\d{3})$", re.I)


def _slot_from_product_id(pid: str) -> Optional[int]:
    m = _P_ID.match((pid or "").strip())
    return int(m.group(1)) if m else None


def _slot_from_rfid_field(rid: str) -> Optional[int]:
    """兼容历史数据：rfid 曾为 P###；新数据为 RFID###。"""
    s = (rid or "").strip()
    m = _P_ID.match(s)
    if m:
        return int(m.group(1))
    m = _RFID_FMT.match(s)
    return int(m.group(1)) if m else None


def collect_used_product_slots() -> set[int]:
    used: set[int] = set()
    for pid, rid in ProductInfo.query.with_entities(ProductInfo.product_id, ProductInfo.rfid_id).all():
        n = _slot_from_product_id(pid)
        if n is not None:
            used.add(n)
        n = _slot_from_rfid_field(rid)
        if n is not None:
            used.add(n)
    return used


def allocate_next_product_codes() -> tuple[str, str]:
    """最小可用槽位：P### 与 RFID### 后三位一致。"""
    used = collect_used_product_slots()
    for n in range(1, 1000):
        if n not in used:
            return f"P{n:03d}", f"RFID{n:03d}"
    raise RuntimeError("无可用产品编号")


def resolve_trace_input_to_rfid(code: str) -> Optional[str]:
    """支持 P001、RFID001，或历史 rfid/product_id 原样匹配。"""
    code = (code or "").strip()
    if not code:
        return None
    m = _P_ID.match(code)
    if m:
        pid = f"P{int(m.group(1)):03d}"
        p = ProductInfo.query.filter_by(product_id=pid).first()
        return p.rfid_id if p else None
    m = _RFID_FMT.match(code)
    if m:
        rid = f"RFID{int(m.group(1)):03d}"
        return rid if ProductInfo.query.filter_by(rfid_id=rid).first() else None
    if ProductInfo.query.filter_by(rfid_id=code).first():
        return code
    p = ProductInfo.query.filter_by(product_id=code).first()
    return p.rfid_id if p else None


def validate_harvest_batch(s: str) -> bool:
    """基地代码 9 位 + 流水号 4 位，共 13 位。"""
    if not s or len(s) != 13:
        return False
    return bool(re.match(r"^[A-Z0-9]{9}\d{4}$", s.upper()))


def count_storage_temp_alerts() -> int:
    """最新仓储温度 >10℃ 或 <0℃ 的产品数量。"""
    n = 0
    for p in ProductInfo.query.all():
        st = (
            StorageData.query.filter_by(rfid_id=p.rfid_id)
            .order_by(StorageData.id.desc())
            .first()
        )
        if not st or st.storage_temp is None:
            continue
        t = float(st.storage_temp)
        if t > 10 or t < 0:
            n += 1
    return n


def _between(v, lo: float, hi: float) -> bool:
    if v is None:
        return True
    try:
        x = float(v)
        return lo <= x <= hi
    except (TypeError, ValueError):
        return True


def count_anomaly_temp_products() -> int:
    """
    行业标准：种植环境温度 20–28℃、仓储 0–8℃、运输 0–10℃。
    任一环节最新数据超出范围则计该产品 1 次（去重）。
    """
    bad: set[str] = set()
    for p in ProductInfo.query.all():
        rfid = p.rfid_id
        pl = (
            PlantingData.query.filter_by(rfid_id=rfid)
            .order_by(PlantingData.id.desc())
            .first()
        )
        if pl and pl.temp is not None and not _between(pl.temp, 20, 28):
            bad.add(rfid)
        st = (
            StorageData.query.filter_by(rfid_id=rfid)
            .order_by(StorageData.id.desc())
            .first()
        )
        if st and st.storage_temp is not None and not _between(st.storage_temp, 0, 8):
            bad.add(rfid)
        tr = (
            TransportData.query.filter_by(rfid_id=rfid)
            .order_by(TransportData.id.desc())
            .first()
        )
        if tr and tr.transport_temp is not None and not _between(tr.transport_temp, 0, 10):
            bad.add(rfid)
    return len(bad)


def count_anomaly_humidity_products() -> int:
    """土壤湿度 50–70%、存储湿度 80–95%，任一超出则计该产品（去重）。"""
    bad: set[str] = set()
    for p in ProductInfo.query.all():
        rfid = p.rfid_id
        pl = (
            PlantingData.query.filter_by(rfid_id=rfid)
            .order_by(PlantingData.id.desc())
            .first()
        )
        if pl and pl.soil_humidity is not None and not _between(pl.soil_humidity, 50, 70):
            bad.add(rfid)
        st = (
            StorageData.query.filter_by(rfid_id=rfid)
            .order_by(StorageData.id.desc())
            .first()
        )
        if st and st.storage_humidity is not None and not _between(st.storage_humidity, 80, 95):
            bad.add(rfid)
    return len(bad)


def count_anomaly_water_products() -> int:
    """每日浇水量 400–600ml（最新种植记录）。"""
    n = 0
    for p in ProductInfo.query.all():
        pl = (
            PlantingData.query.filter_by(rfid_id=p.rfid_id)
            .order_by(PlantingData.id.desc())
            .first()
        )
        if not pl or pl.daily_water is None:
            continue
        if not _between(pl.daily_water, 400, 600):
            n += 1
    return n
