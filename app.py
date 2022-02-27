from flask import Flask, render_template, url_for, request, redirect, session, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class EI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    okei = db.Column(db.Integer, primary_key=True)


class TypeOfGoods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)


class Goods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typeOfGoodsId = db.Column(db.Integer, db.ForeignKey('type_of_goods.id'), nullable=False)
    name = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    eiId = db.Column(db.Integer, db.ForeignKey('EI.id'), nullable=False)
    isPreset = db.Column(db.Boolean)


class Shape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)


class Filling(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)


class Creams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)


class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    goodsId = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)


class CakeLayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cakeId = db.Column(db.Integer, db.ForeignKey('cake.id'), nullable=False)
    shapeId = db.Column(db.Integer, db.ForeignKey('shape.id'), nullable=False)
    fillingId = db.Column(db.Integer, db.ForeignKey('filling.id'), nullable=False)
    creamsId = db.Column(db.Integer, db.ForeignKey('creams.id'), nullable=False)
    rank = db.Column(db.Integer, nullable=False)


class DB_Query:
    def __init__(self, query_text="", need_response=False):
        self.query_text = query_text
        self.need_response = need_response

    def GetConnection(self):
        engine = create_engine('sqlite:///base.db')
        con = engine.connect()
        return con

    def RunQuery(self):
        con = self.GetConnection()
        rs = con.execute(self.query_text)
        last_id = rs.lastrowid

        if self.need_response:
            json_answer = "{"
            current_identifier = ""
            for row in rs:
                if row.Identifier != current_identifier:
                    if current_identifier != "":
                        json_answer += "],"
                    current_identifier = row.Identifier
                    json_answer += "\"" + current_identifier + "\"" + ":["
                else:
                    json_answer += ","
                json_answer += "{\"" + "id" + "\":" + str(row.id) + ",\"name\":\"" + row.name + "\"}"
            json_answer += "]}"

            con.close()
            return json_answer

        con.close()
        return last_id  # TODO: Добавить Exception'ы


class DB_Query_LayersParams(DB_Query):
    def __init__(self, query_text="", need_response=True):
        DB_Query.__init__(self, query_text, need_response)
        self.query_text = 'SELECT Creams.id as id, Creams.name as name, "creams" as Identifier FROM Creams ' \
                          'union SELECT Filling.id, Filling.name, "fillings" FROM Filling ' \
                          'union SELECT Shape.id, Shape.name, "shapes" FROM Shape ' \
                          'order by Identifier'


class DB_Query_AddCakeGoods(DB_Query):
    def __init__(self, query_text="", need_response=False, cake_title=""):
        DB_Query.__init__(self, query_text, need_response)

        self.query_text = 'INSERT INTO goods (typeOfGoodsId, name, description, count, eiId, isPreset) ' \
                          'SELECT type_of_goods.id as typeOfGoodsId, "' + cake_title + '" AS name, ' \
                          '"' + cake_title + '" AS description, 1 AS count, EI.id as eiId, false as isPreset ' \
                          'FROM type_of_goods JOIN EI ON TRUE WHERE type_of_goods.name = "Торт" AND EI.okei = 796'


class DB_Query_AddCake(DB_Query):
    def __init__(self, query_text="", need_response=False, cake_title="", goods_id=1):
        DB_Query.__init__(self, query_text, need_response)

        self.query_text = 'INSERT INTO cake (title, goodsId) ' \
                          'VALUES ("' + cake_title + '", ' + str(goods_id) + ')'


class DB_Query_AddCakeLayer(DB_Query):
    def __init__(self, query_text="", need_response=False, cake_id=1, shape_id=1, filling_id=1, creams_id=1, rank=0):
        DB_Query.__init__(self, query_text, need_response)

        self.query_text = 'INSERT INTO cake_layer (cakeId, shapeId, fillingId, creamsId, rank) ' \
                          'VALUES (' + str(cake_id) + ', ' + str(shape_id) + ', ' + str(filling_id) + ', ' \
                          + str(creams_id) + ', ' + str(rank) + ')'


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/products')
def products():
    if request.method == "POST":
        return redirect('/creater')
    else:
        return render_template("products.html")


@app.route('/creater', methods=["POST", "GET"])
def creater():

    if request.method == "POST":

        print(request.form['hiddenJSON'])
        json_data = json.loads(request.form['hiddenJSON'])
        cake_title = json_data['cakeTitle']

        add_cake_goods = DB_Query_AddCakeGoods("", False, cake_title)
        goods_id = add_cake_goods.RunQuery()

        add_cake = DB_Query_AddCake("", False, cake_title, goods_id)
        cake_id = add_cake.RunQuery()

        for cake_layer in json_data['cakeLayers']:
            add_layer = DB_Query_AddCakeLayer("", False, cake_id, cake_layer['shapeId'], cake_layer['fillingId'],
                                              cake_layer['creamsId'], cake_layer['rank'])
            add_layer.RunQuery()

    layers_params = DB_Query_LayersParams()
    json_layers_params = layers_params.RunQuery()

    return render_template("creater.html", json_layers_params=json.loads(json_layers_params))


if __name__ == "__main__":
    app.run(debug=True)
