import flask

import models
import forms
from sqlalchemy.sql import func


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)

# HOME
@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )

#Create Note
@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

#Search notes that use this Tag
@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

#List All Tags
@app.route("/tags")
def allTags_view():
    db = models.db
    tags = db.session.query(models.Tag).all()

    return flask.render_template(
        "allTags_view.html",
        tags=tags,
    )

#Edit Note
@app.route("/notes/edit/<int:noteId>", methods=["GET","POST"])
def edit_note(noteId):
    db=models.db
    note_to_edit = db.session.query(models.Note).get(noteId)
    

    form = forms.NoteForm(object=note_to_edit)
    if form.validate_on_submit():
        note_to_edit.title = form.title.data
        note_to_edit.description = form.description.data

        
        note_to_edit_tags = []
        for tag_name in form.tags.data:
            if tag_name !='':
                tag = (db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name)).scalars().first())

                if not tag:
                    tag = models.Tag(name=tag_name)
                    db.session.add(tag)

                note_to_edit_tags.append(tag)

        note_to_edit.tags = note_to_edit_tags
        note_to_edit.updated_date = func.now()

        db.session.commit()

        return flask.redirect(flask.url_for("index"))
    return flask.render_template("edit_note.html", form=form, note=note_to_edit)

#Edit Tag
@app.route("/tags/edit/<int:tagId>", methods=["GET","POST"])
def edit_Tag(tagId):
    db = models.db

    tag_to_edit = db.session.query(models.Tag).get(tagId)
    form = forms.TagForm()
    if form.validate_on_submit():
        tag_to_edit.name = form.name.data
        db.session.commit()
    return flask.render_template("edit_tag.html",form = form, tag=tag_to_edit)

#Delete Note
@app.route("/notes/delete/<int:noteId>", methods=["GET"])
def delete_note(noteId):
    db = models.db
    note_to_delete = db.session.query(models.Note).get(noteId)

    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

#Delete Tag
@app.route("/tags/delete/<int:tagId>", methods=["GET"])
def delete_tag(tagId):
    db = models.db
    tag_to_delete = db.session.query(models.Tag).get(tagId)
    notes_to_delete_tag = db.session.query(models.Note).filter(models.Note.tags.any(id=tagId)).all()
    for note in notes_to_delete_tag:
        note.tags.remove(tag_to_delete)
    db.session.delete(tag_to_delete)
    db.session.commit()
    return flask.redirect(flask.url_for("allTags_view"))
    
if __name__ == "__main__":
    app.run(debug=True)
