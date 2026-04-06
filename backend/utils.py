from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from models import (
    db,
    PlantingData,
    ProcessData,
    StorageData,
    SalesData,
    TransportData,
    RfidData,
)

# 环节顺序（与 rfid_data.step 一致）
STEP_ORDER = ["种植", "加工", "仓储", "运输", "销售", "已完成"]


def _step_has_table_data(rfid: str, step: str) -> bool:
    """
    判断该环节是否存在“有效业务数据”（不包含“已跳过”）。
    注意：对于可跳过的环节（加工/仓储/运输），我们以最新一条记录为准；
    如果最新记录标记了 skipped，则认为没有业务数据。
    """
    if step == "种植":
        return db.session.query(PlantingData.id).filter_by(rfid_id=rfid).first() is not None
    if step in ("加工", "仓储", "运输"):
        if step == "加工":
            row = (
                ProcessData.query.filter_by(rfid_id=rfid)
                .order_by(ProcessData.id.desc())
                .first()
            )
        elif step == "仓储":
            row = (
                StorageData.query.filter_by(rfid_id=rfid)
                .order_by(StorageData.id.desc())
                .first()
            )
        else:
            row = (
                TransportData.query.filter_by(rfid_id=rfid)
                .order_by(TransportData.id.desc())
                .first()
            )
        if not row:
            return False
        return not bool(getattr(row, "skipped", False))
    if step == "销售":
        return db.session.query(SalesData.id).filter_by(rfid_id=rfid).first() is not None
    if step == "已完成":
        row = db.session.query(RfidData).filter_by(rfid_id=rfid).first()
        return row is not None and row.step == "已完成"
    return False


def _step_is_skipped(rfid: str, step: str) -> bool:
    if step == "加工":
        row = (
            ProcessData.query.filter_by(rfid_id=rfid)
            .order_by(ProcessData.id.desc())
            .first()
        )
        return bool(row and getattr(row, "skipped", False))
    if step == "仓储":
        row = (
            StorageData.query.filter_by(rfid_id=rfid)
            .order_by(StorageData.id.desc())
            .first()
        )
        return bool(row and getattr(row, "skipped", False))
    if step == "运输":
        row = (
            TransportData.query.filter_by(rfid_id=rfid)
            .order_by(TransportData.id.desc())
            .first()
        )
        return bool(row and getattr(row, "skipped", False))
    return False


def last_step_with_data_index(rfid: str) -> Optional[int]:
    """
    在 STEP_ORDER 中，最后一个「有业务数据」的环节下标（0..4 为各业务表，5 为已完成）。
    允许中间环节缺数据：取 max(i)，其中 i 对应环节在库中有记录或 rfid 已标记已完成。
    """
    last = None
    for i, s in enumerate(STEP_ORDER):
        if s == "已完成":
            row = db.session.query(RfidData).filter_by(rfid_id=rfid).first()
            if row and row.step == "已完成":
                last = i
        elif _step_has_table_data(rfid, s):
            last = i
    return last


def step_status_for(rfid: str, step: str) -> str:
    """
    active / completed / fillable / later

    规则（顺序固定：种植 → 加工 → 仓储 → 运输 → 销售 → 已完成）：
    - 无种植数据时，加工～销售、已完成均为 later（不可填）。
    - 有种植后，中间环节可跳过；任意未填环节在「已有种植」前提下可填（fillable），
      中间缺数据的环节也可补填（idx < last 且该环节无数据 → fillable）。
    - 已有数据的环节：若为本环节下标等于 last → active（当前最远环节，可编辑），否则 completed。
    - 被跳过的环节：返回 skipped（不可编辑、不可填报）。
    - 已完成：需先有销售数据才可 fillable；标记完成后为 completed。
    """
    if step not in STEP_ORDER:
        return "later"

    if step in ("加工", "仓储", "运输") and _step_is_skipped(rfid, step):
        return "skipped"

    idx = STEP_ORDER.index(step)
    last = last_step_with_data_index(rfid)

    if step == "已完成":
        row = db.session.query(RfidData).filter_by(rfid_id=rfid).first()
        if row and row.step == "已完成":
            return "completed"
        if _step_has_table_data(rfid, "销售"):
            return "fillable"
        return "later"

    has_planting = _step_has_table_data(rfid, "种植")
    has_step = _step_has_table_data(rfid, step)

    if step == "种植":
        if not has_step:
            return "fillable"
        if last is None:
            return "active"
        if last == 0:
            return "active"
        return "completed"

    if not has_planting:
        return "later"

    if has_step:
        if idx == last:
            return "active"
        return "completed"

    if last is None:
        return "later"

    if idx < last:
        return "fillable"
    if idx > last:
        return "fillable"

    return "later"


def all_step_statuses(rfid: str) -> dict[str, str]:
    return {s: step_status_for(rfid, s) for s in STEP_ORDER}


def ensure_rfid_row(rfid: str, step: str):
    row = db.session.query(RfidData).filter_by(rfid_id=rfid).first()
    if row:
        row.step = step
        row.create_time = datetime.utcnow()
    else:
        db.session.add(RfidData(rfid_id=rfid, step=step, create_time=datetime.utcnow()))


def serialize_decimal(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val


def planting_to_dict(p: PlantingData):
    return {
        "id": p.id,
        "rfid_id": p.rfid_id,
        "daily_water": p.daily_water,
        "light_hour": p.light_hour,
        "temp": serialize_decimal(p.temp),
        "soil_humidity": p.soil_humidity,
        "fertilizer": p.fertilizer,
        "pesticide": p.pesticide,
        "manager": p.manager,
        "operate_time": p.operate_time.isoformat() if p.operate_time else None,
        "harvest_time": p.harvest_time.isoformat() if p.harvest_time else None,
        "create_time": p.create_time.isoformat() if p.create_time else None,
    }


def process_to_dict(p: ProcessData):
    return {
        "id": p.id,
        "rfid_id": p.rfid_id,
        "workshop": p.workshop,
        "clean_method": p.clean_method,
        "process_method": getattr(p, "process_method", None),
        "package_material": p.package_material,
        "quality_result": p.quality_result,
        "report_img": p.report_img,
        "operate_time": p.operate_time.isoformat() if p.operate_time else None,
        "process_start_time": p.process_start_time.isoformat() if p.process_start_time else None,
        "process_end_time": p.process_end_time.isoformat() if p.process_end_time else None,
        "create_time": p.create_time.isoformat() if p.create_time else None,
    }


def storage_to_dict(s: StorageData):
    return {
        "id": s.id,
        "rfid_id": s.rfid_id,
        "warehouse_addr": s.warehouse_addr,
        "storage_temp": serialize_decimal(s.storage_temp),
        "storage_humidity": s.storage_humidity,
        "shelf_life": s.shelf_life,
        "storekeeper": s.storekeeper,
        "operate_time": s.operate_time.isoformat() if s.operate_time else None,
        "in_time": s.in_time.isoformat() if s.in_time else None,
        "out_time": s.out_time.isoformat() if s.out_time else None,
        "create_time": s.create_time.isoformat() if s.create_time else None,
    }


def transport_to_dict(t: TransportData):
    return {
        "id": t.id,
        "rfid_id": t.rfid_id,
        "transport_company": t.transport_company,
        "waybill_no": t.waybill_no,
        "transport_temp": serialize_decimal(t.transport_temp),
        "receiver": t.receiver,
        "track_img": t.track_img,
        "operate_time": t.operate_time.isoformat() if t.operate_time else None,
        "departure_time": t.departure_time.isoformat() if t.departure_time else None,
        "arrive_time": t.arrive_time.isoformat() if t.arrive_time else None,
        "create_time": t.create_time.isoformat() if t.create_time else None,
    }


def sales_to_dict(s: SalesData):
    return {
        "id": s.id,
        "rfid_id": s.rfid_id,
        "store_name": s.store_name,
        "price": serialize_decimal(s.price),
        "seller": s.seller,
        "sale_end_date": s.sale_end_date.isoformat() if s.sale_end_date else None,
        "voucher_img": s.voucher_img,
        "operate_time": s.operate_time.isoformat() if s.operate_time else None,
        "listing_time": s.listing_time.isoformat() if s.listing_time else None,
        "create_time": s.create_time.isoformat() if s.create_time else None,
    }


def parse_operate_time(s) -> Optional[datetime]:
    """解析前端 datetime-local / ISO 字符串（无时区视为本地时间字符串）。"""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    s = str(s).strip()
    if not s:
        return None
    if len(s) == 16 and s[10] == "T":
        s = s + ":00"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def parse_date(s):
    if not s:
        return None
    if isinstance(s, date):
        return s
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


def today_start_utc():
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
