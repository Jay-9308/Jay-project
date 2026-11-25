from flask import Flask, render_template, request, redirect, url_for, flash
import json
import datetime
import os

app = Flask(__name__)
app.secret_key = "hotel123456"
DATA_FILE = "hotel_data.json"

# ========== 原来的核心类 ==========
class Room:
    def __init__(self, room_no, room_type, price, status="空闲"):
        self.room_no = room_no
        self.room_type = room_type
        self.price = price
        self.status = status
    def to_dict(self):
        return vars(self)
    @staticmethod
    def from_dict(d):
        return Room(**d)

class Booking:
    def __init__(self, bid, name, id_card, room_no, checkin, checkout, total_fee):
        self.bid = bid
        self.name = name
        self.id_card = id_card
        self.room_no = room_no
        self.checkin = checkin
        self.checkout = checkout
        self.total_fee = total_fee
        self.status = "booked"
    def to_dict(self):
        return vars(self)
    @staticmethod
    def from_dict(d):
        b = Booking(d["bid"],d["name"],d["id_card"],d["room_no"],d["checkin"],d["checkout"],d["total_fee"])
        b.status = d["status"]
        return b

class Hotel:
    def __init__(self):
        self.rooms = []
        self.bookings = []
        self.next_bid = 1
        self.load_data()

    def save_data(self):
        data = {
            "rooms":[r.to_dict() for r in self.rooms],
            "bookings":[b.to_dict() for b in self.bookings],
            "next_bid":self.next_bid
        }
        with open(DATA_FILE,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE,"r",encoding="utf-8") as f:
                    d = json.load(f)
                self.rooms = [Room.from_dict(x) for x in d["rooms"]]
                self.bookings = [Booking.from_dict(x) for x in d["bookings"]]
                self.next_bid = d["next_bid"]
            except:
                self.init_rooms()
        else:
            self.init_rooms()

    def init_rooms(self):
        self.rooms.clear()
        # 初始化房间
        for n in range(1,9):
            self.rooms.append(Room(str(n),"单人间",120))
        for n in range(9,18):
            self.rooms.append(Room(str(n),"双人间",200))
        for n in range(18,21):
            self.rooms.append(Room(str(n),"豪华套房",380))
        self.save_data()

    def get_room(self,room_no):
        for r in self.rooms:
            if r.room_no == room_no:
                return r
        return None

    def add_booking(self,name,id_card,room_no,checkin,checkout):
        room = self.get_room(room_no)
        if not room or room.status != "空闲":
            return False,"房间不可预订"
        ci = datetime.date.fromisoformat(checkin)
        co = datetime.date.fromisoformat(checkout)
        days = (co - ci).days
        if days <=0:
            return False,"日期错误"
        fee = days * room.price
        b = Booking(self.next_bid,name,id_card,room_no,checkin,checkout,fee)
        self.bookings.append(b)
        room.status = "已预订"
        self.next_bid +=1
        self.save_data()
        return True, b.bid

    def check_in(self,bid):
        for b in self.bookings:
            if b.bid == bid and b.status == "booked":
                b.status = "checked_in"
                self.get_room(b.room_no).status = "已入住"
                self.save_data()
                return True
        return False

    def check_out(self,bid):
        for b in self.bookings:
            if b.bid == bid and b.status == "checked_in":
                b.status = "checked_out"
                self.get_room(b.room_no).status = "清洁中"
                self.save_data()
                return True
        return False

    def cancel_booking(self,bid):
        for b in self.bookings:
            if b.bid == bid and b.status == "booked":
                b.status = "cancelled"
                self.get_room(b.room_no).status = "空闲"
                self.save_data()
                return True
        return False

hotel = Hotel()

# ========== Flask网页路由 ==========
@app.route('/')
def index():
    return render_template("index.html", rooms=hotel.rooms)

@app.route('/book',methods=["GET","POST"])
def book():
    if request.method == "POST":
        name = request.form["name"]
        idc = request.form["idcard"]
        room = request.form["roomno"]
        ci = request.form["checkin"]
        co = request.form["checkout"]
        ok,msg = hotel.add_booking(name,idc,room,ci,co)
        if ok:
            flash(f"预订成功！订单号：{msg}")
        else:
            flash(msg)
        return redirect(url_for("index"))
    free_rooms = [r for r in hotel.rooms if r.status=="空闲"]
    return render_template("book.html",free_rooms=free_rooms)

@app.route('/orders')
def orders():
    return render_template("orders.html", bookings=hotel.bookings)

@app.route('/action/<act>/<int:bid>')
def action(act,bid):
    if act == "in":
        hotel.check_in(bid)
    elif act == "out":
        hotel.check_out(bid)
    elif act == "cancel":
        hotel.cancel_booking(bid)
    return redirect(url_for("orders"))

if __name__ == '__main__':
    app.run(debug=True)