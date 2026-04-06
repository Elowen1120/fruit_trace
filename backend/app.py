import json
import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from api_helpers import allocate_next_product_codes, resolve_trace_input_to_rfid
from models import (
    Comment,
    Complaint,
    EnvReading,
    PlantingData,
    ProcessData,
    ProductInfo,
    RfidData,
    SalesData,
    StorageData,
    TransportData,
    User,
    db,
)
from utils import (
    STEP_ORDER,
    all_step_statuses,
    ensure_rfid_row,
    last_step_with_data_index,
    parse_date,
    parse_operate_time,
    planting_to_dict,
    process_to_dict,
    sales_to_dict,
    serialize_decimal,
    step_status_for,
    storage_to_dict,
    today_start_utc,
    transport_to_dict,
)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fruit-trace-dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@127.0.0.1:3306/fruit_trace?charset=utf8mb4",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

CORS(
    app,
    supports_credentials=True,
    origins=os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(
        ","
    ),
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOW_REPORT_EXT = {"jpg", "jpeg", "png", "pdf"}
ALLOW_IMAGE_EXT = {"jpg", "jpeg", "png"}

PRODUCT_CATEGORIES = frozenset(
    {
        "热带水果",
        "温带水果",
        "柑橘类",
        "叶菜类",
        "根茎类",
        "瓜果类",
        "浆果类",
        "其他",
    }
)


def normalize_product_category(raw):
    s = (raw or "").strip()
    if s in PRODUCT_CATEGORIES:
        return s
    return "其他"


QUALITY_CHECK_LABELS = frozenset({"合格", "不合格"})


def normalize_quality_check(raw):
    s = (raw or "").strip()
    if s in QUALITY_CHECK_LABELS:
        return s
    return "合格"


def parse_required_int(raw, field_cn: str):
    try:
        if raw is None:
            raise ValueError
        s = str(raw).strip()
        if s == "":
            raise ValueError
        return int(float(s)), None
    except (TypeError, ValueError):
        return None, f"{field_cn}须为有效整数"


def parse_optional_decimal(raw, field_cn: str):
    if raw is None or (isinstance(raw, str) and str(raw).strip() == ""):
        return None, None
    try:
        return float(str(raw).strip()), None
    except (TypeError, ValueError):
        return None, f"{field_cn}须为有效数字"


def parse_required_decimal(raw, field_cn: str):
    try:
        if raw is None:
            raise ValueError
        s = str(raw).strip()
        if s == "":
            raise ValueError
        return float(s), None
    except (TypeError, ValueError):
        return None, f"{field_cn}须为有效数字"


def save_step_file(rfid, prefix, file_storage, allowed_ext):
    """保存上传文件，返回 /uploads/ 相对路径；无文件返回 None。"""
    if not file_storage or not file_storage.filename:
        return None
    orig = secure_filename(file_storage.filename)
    if "." not in orig:
        raise ValueError("无效文件名")
    ext = orig.rsplit(".", 1)[-1].lower()
    if ext not in allowed_ext:
        raise ValueError("不支持的文件类型")
    safe_rfid = "".join(c for c in str(rfid) if c.isalnum() or c in ("-", "_"))[:48]
    ts = int(datetime.utcnow().timestamp() * 1000)
    fname = f"{safe_rfid}_{prefix}_{ts}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, fname)
    file_storage.save(path)
    return f"/uploads/{fname}"


def _is_multipart():
    ct = request.content_type or ""
    return "multipart/form-data" in ct


def _resolve_operate_time(raw):
    ot = parse_operate_time(raw)
    return ot if ot is not None else datetime.utcnow()


def _is_duplicate_column_error(exc: Exception) -> bool:
    """MySQL 1060 Duplicate column name"""
    if "Duplicate column" in str(exc) or "1060" in str(exc):
        return True
    orig = getattr(exc, "orig", None)
    if orig is not None and getattr(orig, "args", None):
        return orig.args[0] == 1060
    return False


def ensure_transport_schema():
    """
    旧库若仍为 logistics_data / logistics_company，自动重命名为 transport_data / transport_company，
    并把 rfid_data、env_readings 中的环节「物流」改为「运输」。不删除任何表。
    若已存在 transport_data 且无 logistics_data，则跳过。可重复执行。
    """
    insp = inspect(db.engine)
    names = set(insp.get_table_names())
    if "logistics_data" in names and "transport_data" not in names:
        with db.engine.begin() as conn:
            conn.execute(text("RENAME TABLE logistics_data TO transport_data"))
        app.logger.info("ensure_transport_schema: renamed table logistics_data -> transport_data")
        insp = inspect(db.engine)
        names = set(insp.get_table_names())
    if "transport_data" not in names:
        return
    cols = {c["name"] for c in insp.get_columns("transport_data")}
    if "logistics_company" in cols and "transport_company" not in cols:
        with db.engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE transport_data CHANGE COLUMN logistics_company "
                    "transport_company VARCHAR(50) DEFAULT NULL"
                )
            )
        app.logger.info(
            "ensure_transport_schema: renamed column logistics_company -> transport_company"
        )
    try:
        with db.engine.begin() as conn:
            conn.execute(
                text("UPDATE rfid_data SET step = '运输' WHERE step = '物流'")
            )
            conn.execute(
                text("UPDATE env_readings SET stage = '运输' WHERE stage = '物流'")
            )
    except Exception as e:
        app.logger.warning("ensure_transport_schema: step label update: %s", e)


def ensure_operate_time_columns():
    """旧库未执行 migrate_operate_time.sql 时补全列，避免 ORM 查询 Unknown column 导致 500。"""
    stmts = [
        "ALTER TABLE planting_data ADD COLUMN operate_time DATETIME DEFAULT NULL",
        "ALTER TABLE process_data ADD COLUMN operate_time DATETIME DEFAULT NULL",
        "ALTER TABLE storage_data ADD COLUMN operate_time DATETIME DEFAULT NULL",
        "ALTER TABLE transport_data ADD COLUMN operate_time DATETIME DEFAULT NULL",
        "ALTER TABLE sales_data ADD COLUMN operate_time DATETIME DEFAULT NULL",
    ]
    for sql in stmts:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if _is_duplicate_column_error(e):
                continue
            raise


def ensure_paper_time_columns():
    """补全论文字段所需的时间列（全部允许为空，兼容旧数据）。"""
    stmts = [
        "ALTER TABLE planting_data ADD COLUMN harvest_time DATETIME DEFAULT NULL",
        "ALTER TABLE process_data ADD COLUMN process_method VARCHAR(50) DEFAULT NULL",
        "ALTER TABLE process_data ADD COLUMN process_start_time DATETIME DEFAULT NULL",
        "ALTER TABLE process_data ADD COLUMN process_end_time DATETIME DEFAULT NULL",
        "ALTER TABLE storage_data ADD COLUMN in_time DATETIME DEFAULT NULL",
        "ALTER TABLE storage_data ADD COLUMN out_time DATETIME DEFAULT NULL",
        "ALTER TABLE transport_data ADD COLUMN departure_time DATETIME DEFAULT NULL",
        "ALTER TABLE transport_data ADD COLUMN arrive_time DATETIME DEFAULT NULL",
        "ALTER TABLE sales_data ADD COLUMN listing_time DATETIME DEFAULT NULL",
    ]
    for sql in stmts:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if _is_duplicate_column_error(e):
                continue
            raise


def ensure_skipped_columns():
    """补全管理端“跳过此环节”所需字段（skipped）。"""
    stmts = [
        "ALTER TABLE process_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE storage_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE transport_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0",
    ]
    for sql in stmts:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if _is_duplicate_column_error(e):
                continue
            raise


def ensure_user_auth_schema():
    """用户表 + comments/complaints.user_id（旧库可重复执行）。"""
    insp = inspect(db.engine)
    names = set(insp.get_table_names())
    if "users" not in names:
        with db.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE users (
                      id INT AUTO_INCREMENT PRIMARY KEY,
                      username VARCHAR(10) NOT NULL UNIQUE,
                      password_hash VARCHAR(255) NOT NULL,
                      created_at DATETIME DEFAULT NULL,
                      INDEX idx_users_username (username)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )
        app.logger.info("ensure_user_auth_schema: created users table")
        insp = inspect(db.engine)
    if "comments" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("comments")}
        if "user_id" not in cols:
            try:
                db.session.execute(
                    text("ALTER TABLE comments ADD COLUMN user_id INT DEFAULT NULL")
                )
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if not _is_duplicate_column_error(e):
                    raise
    if "complaints" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("complaints")}
        if "user_id" not in cols:
            try:
                db.session.execute(
                    text("ALTER TABLE complaints ADD COLUMN user_id INT DEFAULT NULL")
                )
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if not _is_duplicate_column_error(e):
                    raise
        if "media" not in cols:
            try:
                db.session.execute(
                    text("ALTER TABLE complaints ADD COLUMN media TEXT DEFAULT NULL")
                )
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if not _is_duplicate_column_error(e):
                    raise


def ensure_product_info_category():
    """product_info.category：果蔬大类（新鲜度按品类温区）；旧库可重复执行。"""
    insp = inspect(db.engine)
    if "product_info" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("product_info")}
    if "category" in cols:
        return
    try:
        db.session.execute(
            text(
                "ALTER TABLE product_info ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT '其他'"
            )
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if not _is_duplicate_column_error(e):
            raise


def validate_complaint_contact(raw):
    """选填；若填写则须为大陆 11 位手机号（1 开头）或含 @ 且前后非空的邮箱。"""
    if raw is None:
        return None, None
    s = (raw or "").strip()
    if not s:
        return None, None
    if re.fullmatch(r"1\d{10}", s):
        return s, None
    if re.fullmatch(r"[^@\s]+@[^@\s]+", s):
        return s, None
    return None, "请填写正确的手机号或邮箱"


db.init_app(app)

with app.app_context():
    try:
        ensure_transport_schema()
    except Exception as e:
        app.logger.warning("ensure_transport_schema: %s", e)
    try:
        ensure_operate_time_columns()
    except Exception as e:
        app.logger.warning("ensure_operate_time_columns: %s", e)
    try:
        ensure_paper_time_columns()
    except Exception as e:
        app.logger.warning("ensure_paper_time_columns: %s", e)

    try:
        ensure_skipped_columns()
    except Exception as e:
        app.logger.warning("ensure_skipped_columns: %s", e)
    try:
        ensure_user_auth_schema()
    except Exception as e:
        app.logger.warning("ensure_user_auth_schema: %s", e)
    try:
        ensure_product_info_category()
    except Exception as e:
        app.logger.warning("ensure_product_info_category: %s", e)


@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    fn = secure_filename(os.path.basename(filename.replace("\\", "/")))
    if not fn or not os.path.isfile(os.path.join(UPLOAD_FOLDER, fn)):
        return jsonify({"ok": False, "error": "文件不存在"}), 404
    return send_from_directory(UPLOAD_FOLDER, fn)


def require_admin():
    if not session.get("admin"):
        return jsonify({"ok": False, "error": "未登录"}), 401
    return None


@app.route("/api/auth/register", methods=["POST"])
def api_auth_register():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or len(username) > 10 or any(ch.isspace() for ch in username):
        return jsonify({"ok": False, "error": "用户名无效：1～10 个字符且不能含空格"}), 400
    if len(password) < 6 or len(password) > 20:
        return jsonify({"ok": False, "error": "密码长度为 6～20 位"}), 400
    u = User(
        username=username,
        password_hash=generate_password_hash(password),
        created_at=datetime.utcnow(),
    )
    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "error": "用户名已存在"}), 400
    return jsonify({"ok": True, "user": {"id": u.id, "username": u.username}})


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"ok": False, "error": "用户名或密码错误"}), 401
    session["user_id"] = u.id
    return jsonify({"ok": True, "user": {"id": u.id, "username": u.username}})


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    session.pop("user_id", None)
    return jsonify({"ok": True})


@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": True, "user": None})
    u = db.session.get(User, uid)
    if not u:
        session.pop("user_id", None)
        return jsonify({"ok": True, "user": None})
    return jsonify({"ok": True, "user": {"id": u.id, "username": u.username}})


def latest_planting(rfid):
    return (
        PlantingData.query.filter_by(rfid_id=rfid).order_by(PlantingData.id.desc()).first()
    )


def latest_process(rfid):
    return (
        ProcessData.query.filter_by(rfid_id=rfid).order_by(ProcessData.id.desc()).first()
    )


def latest_storage(rfid):
    return (
        StorageData.query.filter_by(rfid_id=rfid).order_by(StorageData.id.desc()).first()
    )


def latest_transport(rfid):
    return (
        TransportData.query.filter_by(rfid_id=rfid)
        .order_by(TransportData.id.desc())
        .first()
    )


def latest_sales(rfid):
    return SalesData.query.filter_by(rfid_id=rfid).order_by(SalesData.id.desc()).first()


@app.route("/api/products", methods=["GET"])
def api_products():
    rows = ProductInfo.query.order_by(ProductInfo.product_id.desc()).all()
    return jsonify([p.to_dict() for p in rows])


@app.route("/api/trace", methods=["GET"])
def api_trace():
    raw = request.args.get("rfid", "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "缺少 rfid"}), 400
    rfid = resolve_trace_input_to_rfid(raw)
    if not rfid:
        return jsonify({"ok": False, "error": "未找到产品"}), 404
    product = ProductInfo.query.filter_by(rfid_id=rfid).first()
    if not product:
        return jsonify({"ok": False, "error": "未找到产品"}), 404

    env_rows = (
        EnvReading.query.filter_by(rfid_id=rfid)
        .order_by(EnvReading.stage, EnvReading.sort_order, EnvReading.id)
        .all()
    )
    env_series = {"planting": [], "storage": [], "transport": []}
    _stage_env = {
        "种植": "planting",
        "仓储": "storage",
        "运输": "transport",
        "物流": "transport",  # 兼容迁移前旧数据
    }
    for r in env_rows:
        key = _stage_env.get(r.stage)
        if not key:
            continue
        env_series[key].append(
            {
                "label": r.point_label or "",
                "temp": serialize_decimal(r.temp) if r.temp is not None else None,
                "humidity": r.humidity,
            }
        )

    statuses = all_step_statuses(rfid)
    planting = latest_planting(rfid)
    process = latest_process(rfid)
    storage = latest_storage(rfid)
    transport = latest_transport(rfid)
    # “跳过”后不返回环节详情数据，只保留 step_status 为 skipped
    if process and getattr(process, "skipped", False):
        process = None
    if storage and getattr(storage, "skipped", False):
        storage = None
    if transport and getattr(transport, "skipped", False):
        transport = None
    sales = latest_sales(rfid)

    comments = (
        Comment.query.filter_by(rfid_id=rfid).order_by(Comment.id.desc()).limit(200).all()
    )
    comment_list = []
    for c in comments:
        media_val = c.media
        try:
            media_parsed = json.loads(media_val) if media_val else None
        except json.JSONDecodeError:
            media_parsed = media_val
        comment_list.append(
            {
                "id": c.id,
                "rfid_id": c.rfid_id,
                "user_id": getattr(c, "user_id", None),
                "username": c.username,
                "content": c.content,
                "score": c.score,
                "media": media_parsed,
                "create_time": c.create_time.isoformat() if c.create_time else None,
            }
        )

    return jsonify(
        {
            "ok": True,
            "product": product.to_dict(),
            "step_statuses": statuses,
            "current_step_index": last_step_with_data_index(rfid),
            "planting": planting_to_dict(planting) if planting else None,
            "process": process_to_dict(process) if process else None,
            "storage": storage_to_dict(storage) if storage else None,
            "transport": transport_to_dict(transport) if transport else None,
            "sales": sales_to_dict(sales) if sales else None,
            "comments": comment_list,
            "environment_series": env_series,
        }
    )


@app.route("/api/comment", methods=["POST"])
def api_comment():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "请先登录"}), 401
    u = db.session.get(User, uid)
    if not u:
        session.pop("user_id", None)
        return jsonify({"ok": False, "error": "请先登录"}), 401

    data = request.get_json(force=True, silent=True) or {}
    rfid = (data.get("rfid_id") or data.get("rfid") or "").strip()
    content = (data.get("content") or "").strip()
    score = data.get("score")
    media = data.get("media")

    if not rfid or not ProductInfo.query.filter_by(rfid_id=rfid).first():
        return jsonify({"ok": False, "error": "无效 rfid"}), 400
    if not content:
        return jsonify({"ok": False, "error": "请填写评价内容"}), 400
    try:
        score = int(score)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "评分无效"}), 400
    if score < 1 or score > 5:
        return jsonify({"ok": False, "error": "评分 1-5"}), 400

    media_str = None
    if media is not None:
        media_str = media if isinstance(media, str) else json.dumps(media, ensure_ascii=False)

    c = Comment(
        rfid_id=rfid,
        user_id=u.id,
        username=u.username,
        content=content,
        score=score,
        media=media_str,
        create_time=datetime.utcnow(),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True, "id": c.id})


@app.route("/api/comment/<int:cid>", methods=["DELETE"])
def api_comment_delete_own(cid):
    """当前登录用户仅可删除本人发表的评价（user_id 须匹配）；旧数据无 user_id 不可由此接口删除。"""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "请先登录"}), 401
    row = Comment.query.filter_by(id=cid).first()
    if not row:
        return jsonify({"ok": False, "error": "记录不存在"}), 404
    if row.user_id is None or row.user_id != uid:
        return jsonify({"ok": False, "error": "无权删除该评价"}), 403
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/comment/<int:cid>", methods=["DELETE"])
def api_admin_comment_delete(cid):
    err = require_admin()
    if err:
        return err
    row = Comment.query.filter_by(id=cid).first()
    if not row:
        return jsonify({"ok": False, "error": "记录不存在"}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/step_status", methods=["GET"])
def api_step_status():
    rfid = request.args.get("rfid", "").strip()
    step = request.args.get("step", "").strip()
    if not rfid or not step:
        return jsonify({"ok": False, "error": "缺少参数"}), 400
    return jsonify({"ok": True, "status": step_status_for(rfid, step)})


@app.route("/api/get_step_data", methods=["GET"])
def api_get_step_data():
    rfid = request.args.get("rfid", "").strip()
    step = request.args.get("step", "").strip()
    if not rfid or step not in STEP_ORDER:
        return jsonify({"ok": False, "error": "参数无效"}), 400

    if step == "种植":
        p = latest_planting(rfid)
        return jsonify({"ok": True, "data": planting_to_dict(p) if p else None})
    if step == "加工":
        p = latest_process(rfid)
        if p and getattr(p, "skipped", False):
            p = None
        return jsonify({"ok": True, "data": process_to_dict(p) if p else None})
    if step == "仓储":
        p = latest_storage(rfid)
        if p and getattr(p, "skipped", False):
            p = None
        return jsonify({"ok": True, "data": storage_to_dict(p) if p else None})
    if step == "运输":
        p = latest_transport(rfid)
        if p and getattr(p, "skipped", False):
            p = None
        return jsonify({"ok": True, "data": transport_to_dict(p) if p else None})
    if step == "销售":
        p = latest_sales(rfid)
        return jsonify({"ok": True, "data": sales_to_dict(p) if p else None})
    if step == "已完成":
        row = RfidData.query.filter_by(rfid_id=rfid).first()
        done = row is not None and row.step == "已完成"
        return jsonify(
            {
                "ok": True,
                "data": {"completed": done, "step": row.step if row else None},
            }
        )
    return jsonify({"ok": False, "error": "未知环节"}), 400


@app.route("/api/planting/<rfid>", methods=["POST"])
def api_planting(rfid):
    err = require_admin()
    if err:
        return err
    st = step_status_for(rfid, "种植")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可编辑种植环节"}), 400
    data = request.get_json(force=True, silent=True) or {}
    # 新论文字段：采收时间 harvest_time
    # 兼容旧前端：若未传 harvest_time，则用 operate_time 作为采收时间
    harvest_raw = data.get("harvest_time") or data.get("operate_time")
    ht = _resolve_operate_time(harvest_raw)
    daily_water, err = parse_required_int(data.get("daily_water"), "每日浇水量")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    light_hour, err = parse_required_int(data.get("light_hour"), "每日光照时间")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    soil_humidity, err = parse_required_int(data.get("soil_humidity"), "土壤湿度")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    temp_val, err = parse_optional_decimal(data.get("temp"), "环境温度")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    if st == "active":
        p = latest_planting(rfid)
        if not p:
            return jsonify({"ok": False, "error": "无种植记录可更新"}), 400
        p.daily_water = daily_water
        p.light_hour = light_hour
        p.temp = temp_val
        p.soil_humidity = soil_humidity
        p.fertilizer = data.get("fertilizer") or ""
        p.pesticide = data.get("pesticide") or ""
        p.manager = data.get("manager") or ""
        p.operate_time = ht  # 兼容旧字段
        p.harvest_time = ht
        p.create_time = datetime.utcnow()
    else:
        p = PlantingData(
            rfid_id=rfid,
            daily_water=daily_water,
            light_hour=light_hour,
            temp=temp_val,
            soil_humidity=soil_humidity,
            fertilizer=data.get("fertilizer") or "",
            pesticide=data.get("pesticide") or "",
            manager=data.get("manager") or "",
            operate_time=ht,  # 兼容旧字段
            harvest_time=ht,
            create_time=datetime.utcnow(),
        )
        db.session.add(p)
    ensure_rfid_row(rfid, "种植")
    db.session.commit()
    return jsonify({"ok": True, "id": p.id})


@app.route("/api/process/<rfid>", methods=["POST"])
def api_process(rfid):
    err = require_admin()
    if err:
        return err
    st = step_status_for(rfid, "加工")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可编辑加工环节"}), 400
    report_file = None
    if _is_multipart():
        data = {
            "workshop": (request.form.get("workshop") or "").strip(),
            "clean_method": (request.form.get("clean_method") or "").strip(),
            "process_method": (request.form.get("process_method") or "").strip(),
            "package_material": (request.form.get("package_material") or "").strip(),
            "quality_result": (request.form.get("quality_result") or "").strip(),
            "report_img": (request.form.get("report_img") or "").strip(),
            "operate_time": (request.form.get("operate_time") or "").strip(),  # 兼容旧前端：当作加工开始时间
            "process_start_time": (request.form.get("process_start_time") or "").strip(),
            "process_end_time": (request.form.get("process_end_time") or "").strip(),
        }
        report_file = request.files.get("report_file")
    else:
        data = request.get_json(force=True, silent=True) or {}
        data = {
            "workshop": (data.get("workshop") or "").strip(),
            "clean_method": (data.get("clean_method") or "").strip(),
            "process_method": (data.get("process_method") or "").strip(),
            "package_material": (data.get("package_material") or "").strip(),
            "quality_result": (data.get("quality_result") or "").strip(),
            "report_img": (data.get("report_img") or "").strip(),
            "operate_time": data.get("operate_time"),  # 兼容旧前端：当作加工开始时间
            "process_start_time": data.get("process_start_time"),
            "process_end_time": data.get("process_end_time"),
        }
    # 新论文字段：加工开始/结束时间
    start_raw = data.get("process_start_time") or data.get("operate_time")
    end_raw = data.get("process_end_time")
    start_ot = _resolve_operate_time(start_raw)
    # 新字段允许为空：结束时间缺失时不写入默认当前时间
    end_ot = parse_operate_time(end_raw)
    try:
        saved = save_step_file(rfid, "report", report_file, ALLOW_REPORT_EXT)
        if saved:
            data["report_img"] = saved
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    data["quality_result"] = normalize_quality_check(data.get("quality_result"))
    if st == "active":
        p = latest_process(rfid)
        if not p:
            return jsonify({"ok": False, "error": "无加工记录可更新"}), 400
        p.workshop = data["workshop"]
        p.clean_method = data["clean_method"]
        p.process_method = data.get("process_method") or ""
        p.package_material = data["package_material"]
        p.quality_result = data["quality_result"]
        p.report_img = data["report_img"]
        p.operate_time = start_ot  # 兼容旧字段
        p.process_start_time = start_ot
        p.process_end_time = end_ot
        p.create_time = datetime.utcnow()
    else:
        p = ProcessData(
            rfid_id=rfid,
            workshop=data["workshop"],
            clean_method=data["clean_method"],
            process_method=data.get("process_method") or "",
            package_material=data["package_material"],
            quality_result=data["quality_result"],
            report_img=data["report_img"],
            operate_time=start_ot,  # 兼容旧字段
            process_start_time=start_ot,
            process_end_time=end_ot,
            create_time=datetime.utcnow(),
        )
        db.session.add(p)
    ensure_rfid_row(rfid, "加工")
    db.session.commit()
    return jsonify({"ok": True, "id": p.id})


@app.route("/api/storage/<rfid>", methods=["POST"])
def api_storage(rfid):
    err = require_admin()
    if err:
        return err
    st = step_status_for(rfid, "仓储")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可编辑仓储环节"}), 400
    data = request.get_json(force=True, silent=True) or {}
    # 新论文字段：入库时间 in_time、出库时间 out_time
    # 兼容旧前端：若未传 in_time，则用 operate_time 作为入库时间
    in_raw = data.get("in_time") or data.get("operate_time")
    out_raw = data.get("out_time")
    in_ot = _resolve_operate_time(in_raw)
    # 出库时间允许为空：缺失则不写入
    out_ot = parse_operate_time(out_raw)
    storage_temp, err = parse_required_decimal(data.get("storage_temp"), "存储温度")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    storage_humidity, err = parse_required_int(data.get("storage_humidity"), "存储湿度")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    shelf_life, err = parse_required_int(data.get("shelf_life"), "保质期（天）")
    if err:
        return jsonify({"ok": False, "error": err}), 400
    if st == "active":
        p = latest_storage(rfid)
        if not p:
            return jsonify({"ok": False, "error": "无仓储记录可更新"}), 400
        p.warehouse_addr = data.get("warehouse_addr") or ""
        p.storage_temp = storage_temp
        p.storage_humidity = storage_humidity
        p.shelf_life = shelf_life
        p.storekeeper = data.get("storekeeper") or ""
        p.operate_time = in_ot  # 兼容旧字段
        p.in_time = in_ot
        p.out_time = out_ot
        p.create_time = datetime.utcnow()
    else:
        p = StorageData(
            rfid_id=rfid,
            warehouse_addr=data.get("warehouse_addr") or "",
            storage_temp=storage_temp,
            storage_humidity=storage_humidity,
            shelf_life=shelf_life,
            storekeeper=data.get("storekeeper") or "",
            operate_time=in_ot,  # 兼容旧字段
            in_time=in_ot,
            out_time=out_ot,
            create_time=datetime.utcnow(),
        )
        db.session.add(p)
    ensure_rfid_row(rfid, "仓储")
    db.session.commit()
    return jsonify({"ok": True, "id": p.id})


@app.route("/api/transport/<rfid>", methods=["POST"])
def api_transport(rfid):
    err = require_admin()
    if err:
        return err
    st = step_status_for(rfid, "运输")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可编辑运输环节"}), 400
    track_file = None
    if _is_multipart():
        tt = request.form.get("transport_temp")
        if tt not in (None, ""):
            try:
                transport_temp = float(str(tt).strip())
            except (TypeError, ValueError):
                return jsonify({"ok": False, "error": "运输温度须为有效数字"}), 400
        else:
            transport_temp = None
        data = {
            "transport_company": (request.form.get("transport_company") or "").strip(),
            "waybill_no": (request.form.get("waybill_no") or "").strip(),
            "transport_temp": transport_temp,
            "receiver": (request.form.get("receiver") or "").strip(),
            "track_img": (request.form.get("track_img") or "").strip(),
            "operate_time": (request.form.get("operate_time") or "").strip(),  # 兼容旧前端：当作发货时间
            "departure_time": (request.form.get("departure_time") or "").strip(),
            "arrive_time": (request.form.get("arrive_time") or "").strip(),
        }
        track_file = request.files.get("track_file")
    else:
        data = request.get_json(force=True, silent=True) or {}
        tt_raw = data.get("transport_temp")
        transport_temp_json, err = parse_optional_decimal(tt_raw, "运输温度")
        if err:
            return jsonify({"ok": False, "error": err}), 400
        data = {
            "transport_company": (data.get("transport_company") or "").strip(),
            "waybill_no": (data.get("waybill_no") or "").strip(),
            "transport_temp": transport_temp_json,
            "receiver": (data.get("receiver") or "").strip(),
            "track_img": (data.get("track_img") or "").strip(),
            "operate_time": data.get("operate_time"),  # 兼容旧前端：当作发货时间
            "departure_time": data.get("departure_time"),
            "arrive_time": data.get("arrive_time"),
        }
    dep_raw = data.get("departure_time") or data.get("operate_time")
    arr_raw = data.get("arrive_time")
    dep_ot = _resolve_operate_time(dep_raw)
    # 到达时间允许为空：缺失则不写入
    arr_ot = parse_operate_time(arr_raw)
    try:
        saved = save_step_file(rfid, "track", track_file, ALLOW_IMAGE_EXT)
        if saved:
            data["track_img"] = saved
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    if st == "active":
        p = latest_transport(rfid)
        if not p:
            return jsonify({"ok": False, "error": "无运输记录可更新"}), 400
        p.transport_company = data["transport_company"]
        p.waybill_no = data["waybill_no"]
        p.transport_temp = data["transport_temp"]
        p.receiver = data["receiver"]
        p.track_img = data["track_img"]
        p.operate_time = dep_ot  # 兼容旧字段
        p.departure_time = dep_ot
        p.arrive_time = arr_ot
        p.create_time = datetime.utcnow()
    else:
        p = TransportData(
            rfid_id=rfid,
            transport_company=data["transport_company"],
            waybill_no=data["waybill_no"],
            transport_temp=data["transport_temp"],
            receiver=data["receiver"],
            track_img=data["track_img"],
            operate_time=dep_ot,  # 兼容旧字段
            departure_time=dep_ot,
            arrive_time=arr_ot,
            create_time=datetime.utcnow(),
        )
        db.session.add(p)
    ensure_rfid_row(rfid, "运输")
    db.session.commit()
    return jsonify({"ok": True, "id": p.id})


@app.route("/api/skip/<rfid>/<step>", methods=["POST"])
def api_skip_step(rfid, step):
    """将加工/仓储/运输环节标记为“已跳过”（不可再填写该环节数据）。"""
    err = require_admin()
    if err:
        return err

    step = (step or "").strip()
    allowed = ("加工", "仓储", "运输")
    if step not in allowed:
        return jsonify({"ok": False, "error": "未知/不支持的环节"}), 400

    st = step_status_for(rfid, step)
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可跳过该环节"}), 400

    if step == "加工":
        row = ProcessData.query.filter_by(rfid_id=rfid).order_by(ProcessData.id.desc()).first()
        if row:
            row.skipped = True
        else:
            row = ProcessData(rfid_id=rfid, skipped=True, create_time=datetime.utcnow())
            db.session.add(row)
    elif step == "仓储":
        row = StorageData.query.filter_by(rfid_id=rfid).order_by(StorageData.id.desc()).first()
        if row:
            row.skipped = True
        else:
            row = StorageData(rfid_id=rfid, skipped=True, create_time=datetime.utcnow())
            db.session.add(row)
    else:  # 运输
        row = TransportData.query.filter_by(rfid_id=rfid).order_by(TransportData.id.desc()).first()
        if row:
            row.skipped = True
        else:
            row = TransportData(rfid_id=rfid, skipped=True, create_time=datetime.utcnow())
            db.session.add(row)

    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/sales/<rfid>", methods=["POST"])
def api_sales(rfid):
    err = require_admin()
    if err:
        return err
    st = step_status_for(rfid, "销售")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可编辑销售环节"}), 400
    voucher_file = None
    if _is_multipart():
        pr = request.form.get("price")
        price, err = parse_required_decimal(pr, "售价")
        if err:
            return jsonify({"ok": False, "error": err}), 400
        data = {
            "store_name": (request.form.get("store_name") or "").strip(),
            "price": price,
            "seller": (request.form.get("seller") or "").strip(),
            "sale_end_date": request.form.get("sale_end_date"),
            "voucher_img": (request.form.get("voucher_img") or "").strip(),
            "operate_time": (request.form.get("operate_time") or "").strip(),  # 兼容旧前端：当作上架时间
            "listing_time": (request.form.get("listing_time") or "").strip(),
        }
        voucher_file = request.files.get("voucher_file")
    else:
        raw = request.get_json(force=True, silent=True) or {}
        price, err = parse_required_decimal(raw.get("price"), "售价")
        if err:
            return jsonify({"ok": False, "error": err}), 400
        data = {
            "store_name": (raw.get("store_name") or "").strip(),
            "price": price,
            "seller": (raw.get("seller") or "").strip(),
            "sale_end_date": raw.get("sale_end_date"),
            "voucher_img": (raw.get("voucher_img") or "").strip(),
            "operate_time": raw.get("operate_time"),  # 兼容旧前端：当作上架时间
            "listing_time": raw.get("listing_time"),
        }
    listing_raw = data.get("listing_time") or data.get("operate_time")
    listing_ot = _resolve_operate_time(listing_raw)
    try:
        saved = save_step_file(rfid, "voucher", voucher_file, ALLOW_IMAGE_EXT)
        if saved:
            data["voucher_img"] = saved
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    if st == "active":
        p = latest_sales(rfid)
        if not p:
            return jsonify({"ok": False, "error": "无销售记录可更新"}), 400
        p.store_name = data["store_name"]
        p.price = data["price"]
        p.seller = data["seller"]
        p.sale_end_date = parse_date(data["sale_end_date"])
        p.voucher_img = data["voucher_img"]
        p.operate_time = listing_ot  # 兼容旧字段
        p.listing_time = listing_ot
        p.create_time = datetime.utcnow()
    else:
        p = SalesData(
            rfid_id=rfid,
            store_name=data["store_name"],
            price=data["price"],
            seller=data["seller"],
            sale_end_date=parse_date(data["sale_end_date"]),
            voucher_img=data["voucher_img"],
            operate_time=listing_ot,  # 兼容旧字段
            listing_time=listing_ot,
            create_time=datetime.utcnow(),
        )
        db.session.add(p)
    ensure_rfid_row(rfid, "销售")
    db.session.commit()
    return jsonify({"ok": True, "id": p.id})


@app.route("/api/complete/<rfid>", methods=["POST"])
def api_complete(rfid):
    """将流程标记为「已完成」（需已存在销售数据）。"""
    err = require_admin()
    if err:
        return err
    row = RfidData.query.filter_by(rfid_id=rfid).first()
    if row and row.step == "已完成":
        return jsonify({"ok": False, "error": "流程已完成"}), 400
    st = step_status_for(rfid, "已完成")
    if st not in ("active", "fillable"):
        return jsonify({"ok": False, "error": "当前不可完成流程"}), 400
    if not latest_sales(rfid):
        return jsonify({"ok": False, "error": "请先完成销售环节"}), 400
    ensure_rfid_row(rfid, "已完成")
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/product/add", methods=["POST"])
def api_product_add():
    err = require_admin()
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("product_name") or "").strip()
    addr = (data.get("product_address") or "").strip()
    check_result = normalize_quality_check(data.get("check_result"))
    plot_no = (data.get("plot_no") or "").strip()
    variety = (data.get("variety") or "").strip()
    category = normalize_product_category(data.get("category"))
    plant_raw = data.get("plant_time")
    if not name or not addr or not plot_no or not variety:
        return jsonify({"ok": False, "error": "请填写所有必填项"}), 400
    if not plant_raw:
        return jsonify({"ok": False, "error": "请选择种植日期"}), 400
    plant_time = parse_date(plant_raw)
    if not plant_time:
        return jsonify({"ok": False, "error": "种植日期无效"}), 400

    pid, rfid = allocate_next_product_codes()

    p = ProductInfo(
        product_id=pid,
        rfid_id=rfid,
        product_name=name,
        product_address=addr,
        plant_time=plant_time,
        check_result=check_result,
        plot_no=plot_no,
        variety=variety,
        category=category,
        create_time=datetime.utcnow(),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True, "product": p.to_dict()})


@app.route("/api/product/edit/<pid>", methods=["POST"])
def api_product_edit(pid):
    err = require_admin()
    if err:
        return err
    p = ProductInfo.query.filter_by(product_id=pid).first()
    if not p:
        return jsonify({"ok": False, "error": "产品不存在"}), 404
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("product_name") or "").strip()
    addr = (data.get("product_address") or "").strip()
    check_result = normalize_quality_check(data.get("check_result"))
    plot_no = (data.get("plot_no") or "").strip()
    variety = (data.get("variety") or "").strip()
    plant_raw = data.get("plant_time")
    if not name or not addr or not plot_no or not variety:
        return jsonify({"ok": False, "error": "请填写所有必填项"}), 400
    if not plant_raw:
        return jsonify({"ok": False, "error": "请选择种植日期"}), 400
    pt = parse_date(plant_raw)
    if not pt:
        return jsonify({"ok": False, "error": "种植日期无效"}), 400
    p.product_name = name
    p.product_address = addr
    p.plant_time = pt
    p.check_result = check_result
    p.plot_no = plot_no
    p.variety = variety
    if "category" in data:
        p.category = normalize_product_category(data.get("category"))
    db.session.commit()
    return jsonify({"ok": True, "product": p.to_dict()})


@app.route("/api/product/del/<pid>", methods=["DELETE"])
def api_product_del(pid):
    err = require_admin()
    if err:
        return err
    p = ProductInfo.query.filter_by(product_id=pid).first()
    if not p:
        return jsonify({"ok": False, "error": "产品不存在"}), 404
    rfid = p.rfid_id
    PlantingData.query.filter_by(rfid_id=rfid).delete()
    ProcessData.query.filter_by(rfid_id=rfid).delete()
    StorageData.query.filter_by(rfid_id=rfid).delete()
    TransportData.query.filter_by(rfid_id=rfid).delete()
    SalesData.query.filter_by(rfid_id=rfid).delete()
    Comment.query.filter_by(rfid_id=rfid).delete()
    RfidData.query.filter_by(rfid_id=rfid).delete()
    Complaint.query.filter_by(rfid_id=rfid).delete()
    EnvReading.query.filter_by(rfid_id=rfid).delete()
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True, silent=True) or {}
    u = (data.get("username") or "").strip()
    pw = data.get("password") or ""
    if u == "admin" and pw == "123456":
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "账号或密码错误"}), 401


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return jsonify({"ok": True})


@app.route("/api/admin/me", methods=["GET"])
def api_admin_me():
    return jsonify({"ok": True, "admin": bool(session.get("admin"))})


@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    err = require_admin()
    if err:
        return err
    total_products = ProductInfo.query.count()
    active_steps = 0
    qualified_product_count = 0
    for p in ProductInfo.query.all():
        last = last_step_with_data_index(p.rfid_id)
        if last is not None and STEP_ORDER[last] != "已完成":
            active_steps += 1
        proc = latest_process(p.rfid_id)
        if proc and not getattr(proc, "skipped", False):
            is_qualified = (proc.quality_result or "").strip() == "合格"
        else:
            is_qualified = (p.check_result or "").strip() == "合格"
        if is_qualified:
            qualified_product_count += 1
    start = today_start_utc()
    today_comments = Comment.query.filter(Comment.create_time >= start).count()
    pending_complaints_count = Complaint.query.filter_by(status="待处理").count()
    if total_products == 0:
        product_qualified_rate_pct = None
    else:
        product_qualified_rate_pct = int(
            round(100.0 * qualified_product_count / total_products)
        )

    return jsonify(
        {
            "ok": True,
            "total_products": total_products,
            "active_pipeline_count": active_steps,
            "today_comments": today_comments,
            "pending_complaints_count": pending_complaints_count,
            "product_qualified_rate_pct": product_qualified_rate_pct,
        }
    )


@app.route("/api/complaint", methods=["POST"])
def api_complaint_create():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "请先登录"}), 401
    u = db.session.get(User, uid)
    if not u:
        session.pop("user_id", None)
        return jsonify({"ok": False, "error": "请先登录"}), 401

    data = request.get_json(force=True, silent=True) or {}
    rfid = (data.get("rfid_id") or "").strip()
    ctype = (data.get("complaint_type") or "").strip()
    content = (data.get("content") or "").strip()
    contact, contact_err = validate_complaint_contact(data.get("contact"))
    if contact_err:
        return jsonify({"ok": False, "error": contact_err}), 400
    if not rfid or not ProductInfo.query.filter_by(rfid_id=rfid).first():
        return jsonify({"ok": False, "error": "无效产品"}), 400
    if ctype not in ("变质", "包装破损", "疑似假货", "其他"):
        return jsonify({"ok": False, "error": "问题类型无效"}), 400
    if not content:
        return jsonify({"ok": False, "error": "请填写投诉内容"}), 400

    media_raw = data.get("media")
    media_str = None
    if media_raw is not None and media_raw != "":
        if isinstance(media_raw, list):
            media_str = json.dumps(media_raw, ensure_ascii=False)
        elif isinstance(media_raw, str):
            media_str = media_raw

    row = Complaint(
        rfid_id=rfid,
        user_id=u.id,
        complaint_type=ctype,
        content=content,
        contact=contact,
        media=media_str,
        status="待处理",
        create_time=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return jsonify({"ok": True, "id": row.id})


@app.route("/api/complaints", methods=["GET"])
def api_complaints_list():
    err = require_admin()
    if err:
        return err
    rows = Complaint.query.order_by(Complaint.id.desc()).limit(500).all()
    items = []
    for r in rows:
        uname = "—"
        rid = getattr(r, "user_id", None)
        if rid:
            cu = db.session.get(User, rid)
            if cu:
                uname = cu.username
        items.append(
            {
                "id": r.id,
                "rfid_id": r.rfid_id,
                "user_username": uname,
                "complaint_type": r.complaint_type,
                "content": r.content,
                "contact": r.contact,
                "media": getattr(r, "media", None),
                "status": r.status,
                "create_time": r.create_time.isoformat() if r.create_time else None,
            }
        )
    return jsonify({"ok": True, "items": items})


@app.route("/api/complaint/process/<int:cid>", methods=["POST"])
def api_complaint_process(cid):
    err = require_admin()
    if err:
        return err
    row = Complaint.query.filter_by(id=cid).first()
    if not row:
        return jsonify({"ok": False, "error": "记录不存在"}), 404
    row.status = "已处理"
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/complaint/<int:cid>", methods=["DELETE"])
def api_complaint_delete(cid):
    err = require_admin()
    if err:
        return err
    row = Complaint.query.filter_by(id=cid).first()
    if not row:
        return jsonify({"ok": False, "error": "记录不存在"}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/product/comment_scores/<path:rfid>", methods=["GET"])
def api_product_comment_scores(rfid):
    err = require_admin()
    if err:
        return err
    if not ProductInfo.query.filter_by(rfid_id=rfid).first():
        return jsonify({"ok": False, "error": "未找到产品"}), 404
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for c in Comment.query.filter_by(rfid_id=rfid).all():
        if 1 <= c.score <= 5:
            dist[c.score] += 1
    return jsonify({"ok": True, "distribution": dist})


@app.route("/api/admin/comments", methods=["GET"])
def api_admin_comments_list():
    err = require_admin()
    if err:
        return err
    rows = Comment.query.order_by(Comment.id.desc()).limit(500).all()
    rfids = {c.rfid_id for c in rows}
    products_by_rfid = {}
    if rfids:
        for p in ProductInfo.query.filter(ProductInfo.rfid_id.in_(rfids)).all():
            products_by_rfid[p.rfid_id] = p
    items = []
    for c in rows:
        display = c.username
        uid_c = getattr(c, "user_id", None)
        if uid_c:
            cu = db.session.get(User, uid_c)
            if cu:
                display = cu.username
        media_val = c.media
        try:
            media_parsed = json.loads(media_val) if media_val else None
        except json.JSONDecodeError:
            media_parsed = media_val
        prod = products_by_rfid.get(c.rfid_id)
        items.append(
            {
                "id": c.id,
                "rfid_id": c.rfid_id,
                "username": display,
                "user_id": uid_c,
                "product_name": prod.product_name if prod else None,
                "product_id": prod.product_id if prod else None,
                "content": c.content,
                "score": c.score,
                "media": media_parsed,
                "create_time": c.create_time.isoformat() if c.create_time else None,
            }
        )
    return jsonify({"ok": True, "items": items})


@app.route("/api/product/step_meta", methods=["GET"])
def api_product_step_meta():
    """管理端表格：每个产品的环节按钮状态。"""
    err = require_admin()
    if err:
        return err
    products = ProductInfo.query.order_by(ProductInfo.product_id.desc()).all()
    out = []
    for p in products:
        out.append(
            {
                "product": p.to_dict(),
                "steps": all_step_statuses(p.rfid_id),
            }
        )
    return jsonify({"ok": True, "items": out})


@app.cli.command("init-db")
def init_db():
    """创建表结构（需已存在数据库）。"""
    with app.app_context():
        db.create_all()
        print("Tables created.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
