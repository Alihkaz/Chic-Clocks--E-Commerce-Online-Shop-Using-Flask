#
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField , SelectField , FileField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileRequired , FileAllowed 


# WTForm for creating a product post
class CreateProductForm(FlaskForm):

    title = StringField("Product Name", validators=[DataRequired()])
    description = CKEditorField("Product Description" , validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    image = FileField( "Image",validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')]) # IMAGE
    submit = SubmitField("Add Product")



    
    


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")




# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LogIn!")



# Create a form to login existing users
class CategoryForm(FlaskForm):
    name = StringField("Name Of The New Category", validators=[DataRequired()])
    submit = SubmitField("Add Category!")


# WTForm for creating a product post
class EditProductForm(FlaskForm):

    title = StringField("Product Name", validators=[DataRequired()])
    description = CKEditorField("Product Description" , validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    submit = SubmitField("Add Product")




# WTForm for creating an about post
class CreateAboutForm(FlaskForm):

    title = StringField("Title", validators=[DataRequired()])
    description = CKEditorField("About The Brand" , validators=[DataRequired()])
    submit = SubmitField("Submit")
