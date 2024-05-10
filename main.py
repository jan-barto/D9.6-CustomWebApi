from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_bootstrap import Bootstrap5
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = "123456789"
bootstrap = Bootstrap5(app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Recipe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    ingredients: Mapped[str] = mapped_column(String(500), nullable=False)
    procedure: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


# HTTP GET - Read random record
@app.route("/random")
def get_random_recipe():
    result = db.session.execute(db.select(Recipe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)

    return jsonify(Recipe=random_cafe.to_dict())


# HTTP GET - Read all records
@app.route("/all")
def get_all_recipes():
    result = db.session.execute(db.select(Recipe))
    all_cafes = result.scalars().all()
    all_cafes_list = [recipe.to_dict() for recipe in all_cafes]

    return jsonify(recipes=all_cafes_list)


# HTTP GET - Search record
@app.route("/search")
def search_a_recipe():
    keyword = request.args.get('keyword')

    if not keyword:
        error_msg = {"error": {"Bad Request": "Please provide 'keyword' parameter in the URL"}}
        return jsonify(error_msg), 400

    recipes = db.session.query(Recipe).filter(
        Recipe.name.ilike(f"%{keyword}%") |
        Recipe.ingredients.ilike(f"%{keyword}%") |
        Recipe.procedure.ilike(f"%{keyword}%")
    ).all()

    if recipes:
        all_recipes_list = [recipe.to_dict() for recipe in recipes]
        return jsonify(recipes=all_recipes_list)
    else:
        error_msg = {"error": {"Not found": "We did not find any recipe with given keyword."}}
        return error_msg, 404


api_key = "test"


# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def add_a_recipe():
    provided_key = request.args.get('key')
    try:
        if provided_key == api_key:
            new_entry = Recipe(
                name=request.form.get("name"),
                ingredients=request.form.get("ingredients"),
                procedure=request.form.get("procedure"),
                source=request.form.get("source"),
            )
            db.session.add(new_entry)
            db.session.commit()
            return jsonify(response={"success": {"Recipe loaded": "Successfully added the new Recipe."}})
    except Exception as e:
        error_msg = {"error": {"Not processed": f"Error occurred while adding recipe: {str(e)}"}}
        return error_msg
    else:
        error_msg = {"error": {"Not authorized": "Your key does not match."}}
        return error_msg, 401


# HTTP PUT/PATCH - Update Record
@app.route("/update", methods=["POST", "PATCH"])
def update_the_recipe():
    error_msg = None
    recipe_to_update = None
    provided_key = request.args.get('key')
    if provided_key != api_key:
        error_msg = {"error": {"Not authorized": "Your key does not match."}}

    data = request.get_json()
    if "id" in data:
        recipe_to_update_id = data["id"]
        recipe_to_update = db.session.execute(db.select(Recipe).where(Recipe.id == recipe_to_update_id)).scalar()
        if not recipe_to_update:
            error_msg = {"error": {"recipe not found": "No recipe with given ID found."}}
    else:
        error_msg = {"error": {"Missing information": "ID of recipe to update not found.."}}

    if error_msg:
        return error_msg

    try:
        if "name" in data:
            recipe_to_update.name = data["name"]
        if "ingredients" in data:
            recipe_to_update.ingredients = data["ingredients"]
        if "procedure" in data:
            recipe_to_update.procedure = data["procedure"]
        if "source" in data:
            recipe_to_update.source = data["source"]
        db.session.commit()
        return jsonify(response={"success": "Successfully deleted chosen recipe."})
    except Exception as e:
        error_msg = {"error": "Delete failed", "message": str(e)}
        return error_msg


# HTTP DELETE - Delete Record
@app.route("/delete", methods=["DELETE"])
def delete_recipe():
    error_msg = None
    recipe_to_delete = None
    provided_key = request.args.get('key')
    if provided_key != api_key:
        error_msg = {"error": {"Not authorized": "Your key does not match."}}

    data = request.get_json()
    if "id" in data:
        recipe_to_delete_id = data["id"]
        recipe_to_delete = db.session.execute(db.select(Recipe).where(Recipe.id == recipe_to_delete_id)).scalar()
        if not recipe_to_delete:
            error_msg = {"error": {"recipe not found": "No recipe with given ID found."}}
    else:
        error_msg = {"error": {"Missing information": "ID of recipe to update not found.."}}

    if error_msg:
        return error_msg

    try:
        db.session.delete(recipe_to_delete)
        db.session.commit()
        return jsonify(response={"success": "Successfully deleted selected Recipe."}), 200
    except Exception as e:
        error_msg = {"error": "Delete failed", "message": str(e)}
        return error_msg


@app.route("/import")
def import_recipes():
    from data import r
    for item in r:
        new_entry = Recipe(
            name=item[0],
            ingredients=item[1],
            procedure=item[2],
            source=item[3]
        )
        db.session.add(new_entry)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
