from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ProductInfo(db.Model):
    __tablename__ = "product_info"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    rfid_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_address = db.Column(db.String(200))
    plant_time = db.Column(db.Date)
    check_result = db.Column(db.String(20))
    plot_no = db.Column(db.String(50))
    variety = db.Column(db.String(50))
    category = db.Column(db.String(50), nullable=False, server_default="其他", default="其他")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "rfid_id": self.rfid_id,
            "product_name": self.product_name,
            "product_address": self.product_address,
            "plant_time": self.plant_time.isoformat() if self.plant_time else None,
            "check_result": self.check_result,
            "plot_no": self.plot_no,
            "variety": self.variety,
            "category": self.category or "其他",
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class RfidData(db.Model):
    __tablename__ = "rfid_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    step = db.Column(db.String(20), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class PlantingData(db.Model):
    __tablename__ = "planting_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    daily_water = db.Column(db.Integer)
    light_hour = db.Column(db.Integer)
    temp = db.Column(db.Numeric(4, 1))
    soil_humidity = db.Column(db.Integer)
    fertilizer = db.Column(db.String(100))
    pesticide = db.Column(db.String(200))
    manager = db.Column(db.String(50))
    operate_time = db.Column(db.DateTime)
    harvest_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class ProcessData(db.Model):
    __tablename__ = "process_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    # 管理端可将该环节显式标记为“跳过”，此时用户端只显示“已跳过”状态，不显示环节详情数据
    skipped = db.Column(db.Boolean, default=False)
    workshop = db.Column(db.String(50))
    clean_method = db.Column(db.String(50))
    process_method = db.Column(db.String(50))
    package_material = db.Column(db.String(50))
    quality_result = db.Column(db.String(20))
    report_img = db.Column(db.Text)
    operate_time = db.Column(db.DateTime)
    process_start_time = db.Column(db.DateTime)
    process_end_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class StorageData(db.Model):
    __tablename__ = "storage_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    skipped = db.Column(db.Boolean, default=False)
    warehouse_addr = db.Column(db.String(100))
    storage_temp = db.Column(db.Numeric(4, 1))
    storage_humidity = db.Column(db.Integer)
    shelf_life = db.Column(db.Integer)
    storekeeper = db.Column(db.String(50))
    operate_time = db.Column(db.DateTime)
    in_time = db.Column(db.DateTime)
    out_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class TransportData(db.Model):
    __tablename__ = "transport_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    skipped = db.Column(db.Boolean, default=False)
    transport_company = db.Column(db.String(50))
    waybill_no = db.Column(db.String(50))
    transport_temp = db.Column(db.Numeric(4, 1))
    receiver = db.Column(db.String(50))
    track_img = db.Column(db.Text)
    operate_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    arrive_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class SalesData(db.Model):
    __tablename__ = "sales_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    store_name = db.Column(db.String(100))
    price = db.Column(db.Numeric(8, 2))
    seller = db.Column(db.String(50))
    sale_end_date = db.Column(db.Date)
    voucher_img = db.Column(db.Text)
    operate_time = db.Column(db.DateTime)
    listing_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    media = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    complaint_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    contact = db.Column(db.String(100))
    media = db.Column(db.Text)
    status = db.Column(db.String(20), default="待处理")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class EnvReading(db.Model):
    """各环节温湿度波动记录（展示与新鲜度分析）"""

    __tablename__ = "env_readings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rfid_id = db.Column(db.String(50), nullable=False, index=True)
    stage = db.Column(db.String(20), nullable=False)
    point_label = db.Column(db.String(50))
    temp = db.Column(db.Numeric(5, 2))
    humidity = db.Column(db.Integer)
    sort_order = db.Column(db.Integer, default=0)
