#
import datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request 
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash 
from sqlalchemy.orm import relationship
from forms import CreateProductForm, RegisterForm, LoginForm , CategoryForm , EditProductForm , CreateAboutForm , SearchForm
import os
import stripe
from werkzeug.utils import secure_filename





#authentication keys special for the payment api(Stripe)
#NOTE THE TYPE OF THE KEY IS testing key
# setting up Stripe

# PUBLISHABLE_KEY=os.environ.get('PUBLISHABLE_KEY')
# SECRET_KEY=os.environ.get('SECRET_KEY')

#note : this stripe paymant keys are sepcial for testing , and for performing a demo payment 
# if you want to accept an acual payment , just substitute the testing keys(standard keys) by restricted keys 
#and we will add this info in the upcoming updates  # data-shipping-address="true"
    #           data-zip-code="true"
    #           data-allow-remember-me="true"



stripe_keys = {
        "secret_key": os.environ.get('secret_key'),
        "publishable_key": os.environ.get('publishable_key'),
    }

stripe.api_key = stripe_keys['secret_key']



app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

#-----------------------------------------------------------------------------------------------#
# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


#---------------------------------------------------------------------------------------------------------#

# CONNECT TO DB
UPLOAD_PATH='static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get("DB_URI", "sqlite:///products.db") 
app.config['UPLOAD_PATH']=UPLOAD_PATH
db = SQLAlchemy()
db.init_app(app)



#----------------------------------Creating Relational DataBases------------------------------------------#
#---------------------------------------------------------------------------------------------------------#


# CONFIGURE TABLES
class Products(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
 
    category_id=db.Column(db.Integer,  db.ForeignKey("category.id"))

    title= db.Column(db.String(250),  nullable=False)

    description= db.Column(db.Text, nullable=False)

    category = relationship("Category", back_populates="products")

    price= db.Column(db.Integer, nullable=False)

    image = db.Column(db.String(140)) # IMAGE
   
#    Something of interest is the fact that the image column is a string.
#   This is because we will be storing the path to the image in the static folder to save storage.
#    This path will be a string , It is still possible to store the actual file in the database

   


# Create a category table special for the products
class Category(UserMixin, db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    products=relationship("Products" , back_populates="category")
    




# Create a Cart Table for all the products that the user wants to buy !
class Cart(UserMixin, db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)

    # customer_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # customer = relationship("User", back_populates="carts")
 
    title= db.Column(db.String(250),  nullable=False)

    description= db.Column(db.Text, nullable=False)

    price= db.Column(db.Integer, nullable=False)

    image = db.Column(db.String(140)) #IMAGE  

    


   
  
# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(100))

    name = db.Column(db.String(100))

    # carts=relationship("Cart" , back_populates="customer")
    

# Create a category table special for the products
class About(UserMixin, db.Model):
    __tablename__ = "about"

    id = db.Column(db.Integer, primary_key=True)

    title= db.Column(db.String(250),  nullable=False)

    description= db.Column(db.Text, nullable=False)



   
    
    




#-----------------------------------------------------------------------------------------------#



with app.app_context():
    db.create_all()


# Create an admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


#--------------------------------------Authentication after filling the data-------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        #encryption and decryption
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        # adding the new user to the users database 
        # along with the data we get from the form ! 


        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password)
        

        db.session.add(new_user)
        db.session.commit()


        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("get_store"))
    return render_template("register.html", form=form, current_user=current_user)




#-----------------------------------------------------------------------------------------------#



@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again , or sign-up instead")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_store', current_user=current_user))

    return render_template("login.html", form=form, current_user=current_user)



#----------------------------------------------------------------------------------------------------------#


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_store'))





#------------------------------------------Main Page(for board)-----------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------#



@app.route('/')
def get_store():
    #what we are doing here is first make sure that the user is looged in the authentication module , once he is logged in we get 
    # the id of him , then we search in the data base for the tasks and all data related to the id , by that
    # we create for each user a separate account ! So we are filtering the tasks according to the author id . 

    result = db.session.execute(db.select(Category))
    categories = result.scalars().all()


    productresult = db.session.execute(db.select(Products))
    products = productresult.scalars().all()

    
    cartresult = db.session.execute(db.select(Cart))
    cart_items = cartresult.scalars().all()
    nb_of_cart_items=len(cart_items)


    form=SearchForm()
    if form.validate_on_submit():

        result = db.session.execute(db.select(Products).where(Products.title == form.key.data))
        sresult = result.scalar()
       
        return redirect(url_for("get_product" , search_result=sresult))
        


    return render_template("main.html",
                            categories=categories,
                            products=products,
                            nb_of_cart_items=nb_of_cart_items,
                            form=form)
 


                        
        
        


#-----------------------------------------------------------------------------------------------#



# showing the requested task to see from the board ,
# then getting it bfrom the dayabase , and rendering the details to a special format ! 
@app.route("/post/<int:product_id>", methods=["GET", "POST"])
def show_product_details(product_id):

    requested_product = db.get_or_404(Products, product_id)
   

    return render_template("product_details.html",
                            product=requested_product,
                            current_user=current_user)



#-----------------------------------------------------------------------------------------------#

# Use a decorator so only an admin user can create new produccts posts
#after we display the create form along with the data to be filled 
# we then get that data , and insert them in the product database


#what we are doing with the upload is we get the data from the from of the image , then we are getting the file name ,
#  then we are joining the file name with the path of where the image is saved , 
# then we are attaching the data that we are getting to this name ,
#  then instead of saving the inmmage in the data base , we save the link to it ,
#  by that we save speed , and space in the database ! 
# but you can save the image in the data base , and you need this : db.Column(LargeBinary())


@app.route("/new-product/<int:category_id>", methods=["GET", "POST"])
@admin_only
def add_new_product(category_id):
    form = CreateProductForm()



    if form.validate_on_submit():

        new_product = Products(
            title=form.title.data,
            description=form.description.data,
            category_id=category_id,
            price=form.price.data )


       
        uploaded_image = form.image.data
        print(uploaded_image)

        filename = secure_filename(uploaded_image.filename)

        image_path = os.path.join(UPLOAD_PATH, filename)

        uploaded_image.save(image_path)

        new_product.image = image_path

        path_list = new_product.image.split('/')[1:]

        new_path = '/'.join(path_list)

        # Update the database
        new_product.image = image_path
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("get_store"))
    


    return render_template("create_product.html", form=form, current_user=current_user)

    
   

#-----------------------------------------------------------------------------------------------#

# Use a decorator so only an admin user can edit a post
@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
@admin_only
def edit_product(product_id):

    # what we are doing here is getting the id of the product that the user wants to edit 
    # then fill the data of that product in the form we used to create it with
    # to avoid repition , then we managed to submit to the database the new info of the 
    # product 
    product = db.get_or_404(Products, product_id)
    edit_form = EditProductForm(
                                    title=product.title,
                                    description=product.description,
                                    price=product.price,
                                    )
   
    # here what we are aiming to do is editing or updating the product info in the database with the new data that we get from the 
    # edit form , that is sending the product with a new fresh data about it,
    if edit_form.validate_on_submit():

        product.title = edit_form.title.data
        product.description = edit_form.description.data
        product.price = edit_form.price.data
       
      

        db.session.commit()
        #showing the new look of the editrd product depending on it's ID
        return redirect(url_for("show_product_details", product_id=product.id))
    return render_template("edit_product.html",
                            form=edit_form, 
                            is_edit=True,
                            current_user=current_user)



#-----------------------------------------------------------------------------------------------#


# Use a decorator so only an admin user can delete a product
@app.route("/delete/<int:product_id>")
@admin_only
def delete_product(product_id):
    product_to_delete = db.get_or_404(Products, product_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect(url_for('get_store'))





#------------------------------------Adding New Category---------------------------------------------#
#-----------------------------------------------------------------------------------------------#




@app.route("/new-category", methods=["GET", "POST"])
@admin_only
def add_new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        new_category = Category(
            name=form.name.data)
        

        db.session.add(new_category)
        db.session.commit()


        return redirect(url_for("get_store"))
    return render_template("create_product.html",
                            form=form,
                            current_user=current_user)





#------------------------------------------Delete Category------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------#





 # Use a decorator so only an admin user can delete a category
@app.route("/deleteC/<int:category_id>")
@admin_only
def delete_category(category_id):
    category_to_delete = db.get_or_404(Category, category_id)
    db.session.delete(category_to_delete)
    db.session.commit()
    return redirect(url_for('get_store'))                           










#------------------------------------------About Page------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------#

@app.route("/About" , methods=["GET", "POST"])
def show_About():

    
    aboutresult = db.session.execute(db.select(About))
    aboutdata = aboutresult.scalars().all()

    return render_template("show_about.html",
                            aboutdata=aboutdata,
                            current_user=current_user)





    
#------------------------------------------ Creating About Page------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------------#



@app.route("/createabout" , methods=["GET", "POST"])
@admin_only
def create_about():


    form = CreateAboutForm()
    if form.validate_on_submit():
        new_about = About(
            title=form.title.data,
            description=form.description.data)

        db.session.add(new_about)
        db.session.commit()
        return redirect(url_for("show_About"))
    
    return render_template("create_about.html",
                           form=form)




#------------------------------------------ Editing About Page------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------------#


   

@app.route("/editabout/<int:about_id>" , methods=["GET", "POST"])
@admin_only
def edit_about(about_id):
      
      
    about_to_edit = db.get_or_404(About,about_id)
    edit_form = CreateAboutForm(
                                  title=about_to_edit.title,
                                  description=about_to_edit.description)
   
    # here what we are aiming to do is editing or updating the product info in the database with the new data that we get from the 
    # edit form , that is sending the product with a new fresh data about it,
    if edit_form.validate_on_submit():

        about_to_edit.title = edit_form.title.data
        about_to_edit.description = edit_form.description.data
       
       
        db.session.commit()
        #showing the new look of the editrd product depending on it's ID
        return redirect(url_for("show_About"))
    
    return render_template("create_about.html",
                            form=edit_form, 
                            is_edit=True,
                            current_user=current_user)

    





#------------------------------------------ Add To Cart Module------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#    
@app.route("/add-to-Cart/<int:product_id>" , methods=["GET", "POST"])
def add_to_cart(product_id):

    # if not current_user.is_authenticated:
    #         flash("You need to login or register to Add to cart.")
    #         return redirect(url_for("login"))
    #getting the info about the product that the user wants to add to the cart
    requested_product_to_add = db.get_or_404(Products, product_id)
    
    new_product_in_cart = Cart(
                    title=requested_product_to_add.title,
                    description=requested_product_to_add.description,
                    price=requested_product_to_add.price,
                    image=requested_product_to_add.image,
                     )
    

   #add to the Cart data base the product added to the cart!
    
    db.session.add(new_product_in_cart)
    db.session.commit()
    return redirect(url_for("get_store"))
    


   




#------------------------------------------ show cart module ------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#
@app.route("/Show-Cart" , methods=["GET", "POST"])
def show_cart():


    # if not current_user.is_authenticated:
    #         flash("You need to login or register to Add and go to cart.")
    #         return redirect(url_for("login"))



    result = db.session.execute(db.select(Cart))
    products_in_the_cart = result.scalars().all()

    cart_prices=[product.price for product in products_in_the_cart]
    subtotal=(sum(cart_prices))

    return render_template("show_cart.html",
                            products_in_the_cart=products_in_the_cart,
                            subtotal=subtotal)


#------------------------------------------- Remove From Cart-------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------------------#
@app.route("/deletefrom_cart/<int:product_id>" , methods=["GET", "POST"])
def delete_from_cart(product_id): 


    cart_product_to_delete = db.get_or_404(Cart, product_id)
    db.session.delete(cart_product_to_delete)
    db.session.commit()
    return redirect(url_for('show_cart'))


 
#------------------------------------------ Payments and Shippments------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------#

#what we are doing here is that once the cutomer press on the checkout button in the cart , we will give the stripe form , 
#where first he will press on pay with card , when he press on it , we give him the sripe payment form , if payment is validated 
#the it will be success , and we give to him another format saying that the process is success 
@app.route("/checkout/<int:subtotal>" , methods=["GET", "POST"] )
def checkout(subtotal):

    return render_template("checkout.html" ,
                            key=stripe_keys['publishable_key'],
                            subtotal=subtotal)   




@app.route('/charge', methods=['Get','POST'])
def charge():
        

        result = db.session.execute(db.select(Cart))
        products_in_the_cart = result.scalars().all()
        cart_prices=[product.price for product in products_in_the_cart]
        subtotal=(sum(cart_prices))
        # Amount in cents
        amount = int(subtotal)*100

        customer = stripe.Customer.create(
            email='customer@example.com',
            source=request.form['stripeToken'])


        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description='Flask Charge')

       
        for cart_product_to_delete in products_in_the_cart:
            db.session.delete(cart_product_to_delete)
            db.session.commit()    

        return render_template('sucesspay.html',
                                amount=amount,
                                subtotal=subtotal)

#------------------------------implementing search functionality -------------------------------------#                                

@app.route("/searchproducts/sresult", methods=["GET", "POST"])
def get_product(sresult):
        

        
        
        return render_template("products.html" , result=sresult )


#-----------------------------------------------------------------------------------------------#

if __name__ == "__main__":
    app.run(debug=True, port=5001)