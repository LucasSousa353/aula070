import os
import logging
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests

# Configuração do logger
logging.basicConfig(filename='app.log', level=logging.ERROR)

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    logging.error('Internal Server Error: %s', str(e))
    return render_template('500.html', error=str(e)), 500


def send_simple_message(subject, text):
    # Definir variáveis diretamente no código
    mailgun_domain = 'sandbox98ebae98f8924ba7b83edc8ab6e49b08.mailgun.org'
    mailgun_api_key = 'MINHA_API_KEY'
    api_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

    try:
        response = requests.post(
            api_url,
            auth=("api", mailgun_api_key),
            data={
                "from": f"Aluno IFSP <mailgun@{mailgun_domain}>",
                "to": ["sousa.silva353@gmail.com", "flaskaulasweb@zohomail.com"],
                "subject": subject,
                "text": text
            })

        response.raise_for_status() 
        return 'E-mail enviado com sucesso!'
    except requests.exceptions.RequestException as e:
        return f' ERRO - Verifique se o seu e-mail está verificado na mailgun '


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.name.data).first()
            if user is None:
                user = User(username=form.name.data)
                db.session.add(user)
                db.session.commit()
                session['known'] = False

                # Enviar e-mail usando a função Mailgun e obter resultado
                email_result = send_simple_message(
                    subject="Novo Usuário Registrado",
                    text=f"Um novo usuário foi registrado no site do Lucas PT3019578: {form.name.data}"
                )
                flash(email_result, 'info')

            else:
                session['known'] = True
            session['name'] = form.name.data
            return redirect(url_for('index'))
        except Exception as e:
            # Log do erro e exibição na página
            logging.error('Error during user registration or email sending: %s', str(e))
            flash(f'Ocorreu um erro: {str(e)}', 'error')
            return render_template('index.html', form=form, name=session.get('name'), known=session.get('known', False))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))


if __name__ == '__main__':
    app.run(debug=True)
