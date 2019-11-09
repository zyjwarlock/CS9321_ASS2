from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    # 删除所有的表
    #db.drop_all()
    # 创建表
    #db.create_all()

    #admin = User(username='admin', email='admin@example.com')

    #db.session.add(admin)

    #db.session.commit()

    User.query.all()

    app.run(debug=True)

