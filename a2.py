'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Taiyan Zhu
Student ID: z5089986
'''

import json


from flask import Flask
from flask import request
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import fields
from datetime import datetime
import urllib.request
from xml.dom.minidom import parse
import xml.dom.minidom

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app,
          default = "Assignment2", # Default namespace
          title = "Worldbank Dataset", # Documentation Title
                  description = "This is Assignment 2 implementation." # Documentation Description
          )


# The following is the schema of Book
class WBmodel(db.Model):
    collection_id = db.Column(db.Integer, primary_key=True)
    indicator = db.Column(db.String(80), unique=True, nullable=False)
    indicator_value = db.Column(db.String(120), nullable=False)
    creation_time = db.Column(db.DateTime, nullable=False)
    entries = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return '<WorldBank %r>' % self.indicator

def create_db(db_file):
    if(db_file != ''):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file

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


wmodel = api.model("WorldBank", {
    "indicator_id": fields.String
})

@api.route("/ass")
class WorldBankCollection(Resource):

    @api.response(201, "created")
    @api.response(200, "OK")
    @api.response(404, "error")
    @api.expect(wmodel, validate = True)

    def post(self):
        input = json.loads(request.data)
        indicator = input["indicator_id"]
        data = WBmodel.query.filter(WBmodel.indicator == indicator).first()

        if(data): return {"location": "/ass/" + str(data.indicator)}

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

        collection = WBmodel(indicator=str(indicator), indicator_value="GDP (current US$)", creation_time=time, entries= entries)

        db.session.add(collection)
        db.session.commit()

        res = {}
        res["location"] = "/ass/" + str(collection.collection_id)
        res["collection_id"] = str(collection.collection_id)
        res["creation_time"] = str(current_time)
        res["indicator"] = str(indicator)
        return res, 201

    @api.response(200, "OK")
    @api.response(404, "error")
    def get(self):
        data = WBmodel.query.all()
        if(len(data)<1): return {"message": "There is no collection"}, 404
        res = []
        for e in data:
            wb = {
                "location": "/ass/" + str(e.collection_id),
                "collection_id": str(e.collection_id),
                "creation_time": e.creation_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "indicator": e.indicator
            }
            res.append(wb)
        return res, 200




@api.route("/ass/<string:collection_id>")
@api.param("collection_id", "The collection_id")
class WorldBank(Resource):
    @api.response(200, "OK")
    @api.response(404, "The collection_id cannot be found")
    #@api.doc(description="Q2 delete & Q4 - Retrieve a collection")

    def get(self,  collection_id):
        data = WBmodel.query.filter(WBmodel.collection_id == collection_id).first()
        if(not data): return {"message": "There is no collection"}, 404
        wb = {
            "collection_id" : collection_id,
            "indicator": str(data.indicator),
            "indicator_value": str(data.indicator_value),
            "creation_time" : data.creation_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entries" : data.entries
        }
        return wb, 200

    @api.response(200, "OK")
    @api.response(404, "error")
    def delete(self, collection_id):
        data = WBmodel.query.filter(WBmodel.collection_id == collection_id).first()
        if(data):
            db.session.delete(data)
            db.session.commit()
            return { "message": "Collection = {} is removed from the database!".format(collection_id)}, 200
        return {"message": "Wrong Indicator, please double check."}, 404



@api.route("/ass/<string:collection_id>/<string:year>/<string:country>")
class Query_Year_Country(Resource):
    @api.response(200, "OK")
    @api.response(404, "error")
    def get(self, collection_id, year, country):

        data = WBmodel.query.filter(WBmodel.collection_id == collection_id).all()
        if( len(data) < 1): return {"message": "Wrong Indicator, please double check."}, 404


        for indicator in data:
            for entry in indicator.entries: # collect data by requirement
                if entry["country"] == country and entry["date"] == year:
                    output = {
                        "collection_id": collection_id,
                        "indicator": indicator.indicator,
                        "country": country,
                        "year":entry["date"],
                        "value":entry["value"]
                    }
                    return output, 200


        return  {"message":"No information for {0} in {1}".format(country,year)}, 404



@api.route("/ass/<string:collection_id>/<string:year>")
@api.param("q", "Query")
class Query_Year(Resource):

    @api.response(200, "OK")
    @api.response(404, "error")
    def get(self, collection_id, year):

        query = request.args.get("q")

        data = WBmodel.query.filter(WBmodel.collection_id == collection_id).first()
        if(not data): return {"message": "ID cannot be found in the collection"}, 404
        res = []
        for entry in data.entries:
            if entry["date"] == year :
                res.append(entry)

        if query:
            res = list(filter(lambda x: x["value"] != None, res))

            if "top" in str(query).lower():
                try:
                    N = int(query[3:])
                except:
                    return {"message": "The N should be an integer."}, 404
                res = sorted(res, key = lambda x: float(x["value"]), reverse = True)[:N]

            elif "bottom" in str(query).lower():
                try:
                    N = int(query[6:])
                except:
                    return {"message": "The N should be an integer."}, 404
                res = sorted(res, key = lambda x: float(x["value"]), reverse = False)[:N]
            else:
                 return {"message": "wrong query."}, 404

            if N > 100:
                return {"message": "N should be in range bewteen 1 and 100."}, 404



        return {
                   "indicator": data.indicator,
                   "indicator_value": data.indicator_value,
                   "entries" : res
                }, 200

# if __name__ == '__main__':
#     create_db('data.db')
#     app.run()
