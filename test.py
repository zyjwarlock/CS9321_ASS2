'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Taiyan Zhu
Student ID: z5089986
'''
import sqlite3
import json

from flask import Flask
from flask import request
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import fields
from flask_restplus import inputs
from flask_restplus import reqparse
from datetime import datetime
import urllib.request
from xml.dom.minidom import parse
import xml.dom.minidom

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
api = Api(app,
          default = "Assignment2", # Default namespace
          title = "Worldbank Dataset", # Documentation Title
                  description = "This is Assignment 2 implementation." # Documentation Description
          )


# The following is the schema of Book
class WorldBank(db.Model):
    collection_id = db.Column(db.Integer, primary_key=True)
    indicator = db.Column(db.String(80), unique=True, nullable=False)
    indicator_value = db.Column(db.String(120), nullable=False)
    creation_time = db.Column(db.DateTime, nullable=False)
    entries = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return '<WorldBank %r>' % self.indicator

def create_db(db_file):
    db.drop_all()
    db.create_all()

    urlbyte = urllib.request.urlopen('http://api.worldbank.org/v2/indicators')
    xml_str = urlbyte.read().decode('utf-8')
    output = open('indicators.xml', 'w')
    output.write(xml_str)
    output.close()

    DOMTree = xml.dom.minidom.parse("indicators.xml")
    collection = DOMTree.documentElement

    tags = collection.getElementsByTagName("wb:indicator")

    output_indicators = open('indicators', 'w')

    for e in tags: output_indicators.write(e.getAttribute("id")+'\n')

    output_indicators.close()

    pass 

'''
Put your API code below. No certain requriement about the function name as long as it works.
'''

wmodel = api.model("WorldBank", {
    "indicator_id": fields.String
})

# create_db('')
# indicator_arguments = reqparse.RequestParser()
# indicator_arguments.add_argument('indicator', type=str, required=True)
@api.route("/ass")
class WorldBankCollection(Resource):
    @api.response(201, "created")
    @api.response(200, "OK")
    @api.response(404, "error")
    @api.expect(wmodel, validate = True)
    def post(self):

        input = json.loads(request.data)

        indicator = input["indicator_id"]

        # data = WorldBank.query.filter(WorldBank.indicator == indicator).first()
        #
        # if(data): return {"location": "/ass/" + str(data.indicator)}

        url = "http://api.worldbank.org/v2/countries/all/indicators/" + indicator + "?date=2013:2018&format=json&per_page=2000"

        response = urllib.request.urlopen(url)

        data = json.loads(response.read())

        if(len(data) < 2):
            return {"message": "Wrong Indicator, please double check."}, 404

        time = datetime.now()

        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        entries = []

        for e in data[1]:
            entrie={}
            entrie["country"] = e["country"]["value"]
            entrie["date"] = e["date"]
            entrie["value"] = e["value"]
            entries.append(entrie)

        collection = WorldBank(indicator=str(indicator), indicator_value="GDP (current US$)", creation_time=time, entries=json.dumps(entries))

        db.session.add(collection)
        db.session.commit()

        res = {}

        res["location"] = "/ass/" + str(collection.collection_id)
        res["collection_id"] = str(collection.collection_id)
        res["creation_time"] = str(current_time)
        res["indicator"] = str(indicator)

        return res, 201

        pass

@api.route("/ass/<string:collections_id>")
@api.param("collections_id", "The collection_id")
class WorldBank(Resource):
    @api.response(200, "OK")
    @api.response(404, "The collections_id was not found")
    @api.doc(description="Q2 delete & Q4 - Retrieve a collection")

    def get(self,  collections_id):
        output = []
        data = WorldBank.query.filter(WorldBank.id == collections_id).first()
        for i in data:
            x = {"location": "/ass/"  + str(i['_id']),\
                 "collection_id": str(i['_id']),\
                "creation_time": i['creation_time'],\
                "indicator": i['indicator']
            }
            output.append(x)
        return output, 200

    def delete(self, collections_id):
        try:
            data = WorldBank.query.filter(WorldBank.id == collections_id).first()
            return data, 200
        except:
            return {"message": "Wrong Indicator, please double check."}, 404



@api.route("/ass2/<string:collections_id>/<string:year>")
class Query_Year(Resource):
    def get(self, collections_id, year):
        query = request.args.get("query")
        find = c.find({"_id": ObjectId(collections_id)})
        output = []
        for i in find:
            for data in i["entries"]:
                if data["date"] == year:
                    output.append(data)
        if query:
            if "top" in query:
                output = sorted(output, key=lambda i: float(i["value"]), reverse = True)
                try:
                    N = int(query[3:])
                except:
                    return {"message": "The N should be an integer."}, 404
            elif "bottom" in query:
                output = sorted(output, key=lambda i: float(i["value"]), reverse = False)
                try:
                    N = int(query[6:])
                except:
                    return {"message": "The N should be an integer."}, 404
            else:
                 return {"message": "wrong query."}, 404
            if N > 100:
                return {"message": "N should be in range bewteen 1 and 100."}, 404
            return output[:N], 200

if __name__ == '__main__':
    create_db('')
    app.run()
