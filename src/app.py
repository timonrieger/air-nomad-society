from flask import Flask, redirect, render_template, flash, request, url_for
from src.utility.forms import AirNomadSocietyForm
from flask_bootstrap import Bootstrap5
from src.utility.helpers import generate_token
from flask_wtf.csrf import CSRFProtect
from database import db, create_all, AirNomads
import os
from flask_caching import Cache
from src.utility.constants import DB_URI, SECRET_KEY

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SECRET_KEY'] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
db.init_app(app)
bootstrap = Bootstrap5(app)

csrf = CSRFProtect()
csrf.init_app(app)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

with app.app_context():
    create_all(app)
    

@app.route("/", methods=["GET"])
@cache.cached(timeout=60 * 60 * 24 * 7 * 52)
def home():
    return render_template("index.html")


@app.route("/subscribe", methods=["POST", "GET"])
def subscribe():
    token = request.args.get("token")
    id = request.args.get("id")
    unsubscribe = request.args.get("unsubscribe")
    form = AirNomadSocietyForm()

    if (token or id) and request.method == "GET":
        member = None
        if token:
            member = AirNomads.query.filter_by(token=token).scalar()
        elif id:
            member = AirNomads.query.filter_by(id=id).scalar()

        if not member:
            flash("No member found. Please subscribe to become a member.", category="error")
            return render_template("subscribe.html", form=form, show_form=True)

        elif member and unsubscribe:
            form = AirNomadSocietyForm(
                username=member.username,
                email=member.email,
                departure_city=f"{member.departure_city} | {member.departure_iata}",
                currency=member.currency,
                min_nights=member.min_nights,
                max_nights=member.max_nights,
                min_days_ahead=member.min_days_ahead,
                max_days_ahead=member.max_days_ahead,
                favorite_countries=[country.strip() for country in member.travel_countries.split(",")],
                excluded_countries=[country.strip() for country in (member.excluded_countries.split(",") if member.excluded_countries else [])]
            )
            db.session.delete(member)
            db.session.commit()
            flash(f"You have successfully unsubscribed with {member.email}.", category="success")
            flash("Unsubscribed by mistake? To resubscribe, simply submit the form again.")


            return render_template("subscribe.html", form=form, show_form=True)

        elif member and token and not unsubscribe: #user clicked update link in email
            form = AirNomadSocietyForm(
                username=member.username,
                email=member.email,
                departure_city=f"{member.departure_city} | {member.departure_iata}",
                currency=member.currency,
                min_nights=member.min_nights,
                max_nights=member.max_nights,
                min_days_ahead=member.min_days_ahead,
                max_days_ahead=member.max_days_ahead,
                favorite_countries=[country.strip() for country in member.travel_countries.split(",")],
                excluded_countries=[country.strip() for country in (member.excluded_countries.split(",") if member.excluded_countries else [])]
            )
            flash("Your profile is ready for updates. Please make any changes as needed.", category="success")
            return render_template("subscribe.html", form=form, show_form=True, update=True)

        else:
            return render_template("subscribe.html", form=form)

    if form.validate_on_submit() and request.method == 'POST':
        already_member = AirNomads.query.where(AirNomads.email == form.email.data).scalar()
        favorite_countries = ",".join([country for country in form.favorite_countries.data])
        excluded_countries = ",".join([country for country in form.excluded_countries.data]) if form.excluded_countries.data else None
        if already_member:
            already_member.username = form.username.data
            already_member.departure_city = form.departure_city.data.split(" | ")[0]
            already_member.departure_iata = form.departure_city.data.split(" | ")[1]
            already_member.currency = form.currency.data
            already_member.min_nights = form.min_nights.data
            already_member.max_nights = form.max_nights.data
            already_member.min_days_ahead = form.min_days_ahead.data
            already_member.max_days_ahead = form.max_days_ahead.data
            already_member.travel_countries = favorite_countries
            already_member.excluded_countries = excluded_countries
            db.session.commit()
            flash("Your preferences were changed successfully.", category="success")
            return render_template("subscribe.html", form=form, update=True)
        if not already_member:
            new_member = AirNomads(
                username=form.username.data,
                email=form.email.data,
                departure_city=form.departure_city.data.split(" | ")[0],
                departure_iata=form.departure_city.data.split(" | ")[1],
                currency=form.currency.data,
                min_nights=form.min_nights.data,
                max_nights=form.max_nights.data,
                min_days_ahead=form.min_days_ahead.data,
                max_days_ahead=form.max_days_ahead.data,
                travel_countries=favorite_countries,
                excluded_countries=excluded_countries,
                token=generate_token()
            )
            db.session.add(new_member)
            db.session.commit()
            flash(f"Successfully subscribed with {new_member.email}.", category="success")
            
        return render_template("subscribe.html", form=form)

    return render_template("subscribe.html", form=form, show_form=True)

@app.route("/unsubscribe")
def unsubscribe_users():
    token = request.args.get("token")
    member = AirNomads.query.where(AirNomads.token == token).scalar()
    
    if member:
        return redirect(url_for("subscribe", token=token, unsubscribe=True))
    if not member:
        flash("You are already unsubscribed.", category="error")
        return redirect(url_for("subscribe"))

@app.route("/example")
def example():
    return render_template("example_email.html")

@app.after_request
def add_header(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

if __name__ == "__main__":
    app.run(debug=False)
