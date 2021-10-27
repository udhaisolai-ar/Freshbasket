from flask import *
from freshbasket_recommendation import *
from collections import Counter
from twilio.rest import Client
import pymysql
import os
from datetime import timedelta,datetime
from dotenv import *

#Initializing Variables and Lists
c=0 
otp=""
dictItems=[]
ordersummary=[]
dictItemsCopy=[]
contactdetails=[]


#Retrieving Enivronmental Variables form .env
load_dotenv()
db_Password=os.getenv('dbp')
db_User=os.getenv('dbU')
db=os.getenv('db')

#DB connection
con=pymysql.connect(host='localhost',user=db_User,password=db_Password,db=db)
cur=con.cursor()

#Session Config
Flask.secret_key=os.getenv("secretKey")
Flask.permanent_session_lifetime=timedelta(minutes=3)
Flask.session_refresh_each_request = True


#Creating Blueprint
freshbasket_blueprint=Blueprint("freshbasket_blueprint",__name__)


#rendering (index)index_proj.html
@freshbasket_blueprint.route("/",methods=["GET"])
def index():
   global c
   c+=1
   session['qty']=c+1
   
   cur.execute("select * from products_details limit 9")
   data=cur.fetchall()
   
   a=[]
   for row in data:
    a.append(row)
   session['quant']=request.form.get('qty')
   return render_template("index_proj.html",li=a,length=len(a))

#Rendering INDEX with More Products
@freshbasket_blueprint.route("/<count>",methods=["GET"])
def index1(count):
   global c
   c+=1
   session['qty']=c+1
   
   cur.execute("select * from products_details")
   data=cur.fetchall()
   
   a=[]
   for row in data:
    a.append(row)
   
   session['quant']=request.form.get('qty')
   
   return render_template("index_proj.html",li=a,length=len(a))

#Rendering PRODUCTPAGE with Product Recommendation
#routing to the /products/<variable> page (ref : href in html , example : href="products/apple")
@freshbasket_blueprint.route("/products/<product_name>")
def product(product_name):
    #fetching records based on product_name
    
    if product_name=='sweetlime':
          product_name='sweet lime'
    
    cur.execute("select * from products_details where product_name= %s",product_name)
    data=cur.fetchall()
    for row in data:
       images = row[3]
       price=row[2]
       name=row[1] 
    
    #Recommendation Products
    recommendationItems=recommendation(product_name,datetime.today().month)
      
    products_db=[]
    for i in range(len(recommendationItems)):
        row_data=recommendationItems[i]
        cur.execute("select * from products_details where product_name= %s",row_data)
        products_db.append(cur.fetchone())

    return render_template("product-detail.html",img=images,value=name.upper(),
                           price=price,db=products_db,length=len(products_db))#return productdetail page with multiple parameters used in html


#Add To Cart
@freshbasket_blueprint.route("/Addcart/<product_name>",methods=["POST"])
def Addcart(product_name):
   dictItemsCopy.append(product_name.lower())
   session['CartQty']=dictItemsCopy
   ordersummary.append(session['CartQty'])
   
   if product_name not in dictItems:
    dictItems.append(str(product_name.lower()))
    if 'dictItems' in session:
     print(session['CartItems']) 
    else:
     session['CartItems']=dictItems
     
    return redirect(request.referrer) #review code later
   
   else:
      return redirect(request.referrer)


@freshbasket_blueprint.route("/cart")
def cart():
   ItemQtyList=ItemQtyfunc(dictItemsCopy)
   ItemQtyList1=list(ItemQtyList.values())
   params=dictItems
   
   if len(ordersummary)!=0:
      query='SELECT * FROM products_details WHERE product_name IN ({}) order by product_id desc'.format(','.join(['%s']*len(params)))
      cur.execute(query, params)
      data=cur.fetchall()
      
      a=[]
      price=[]
      
      for row in data:
         a.append(row)
         price.append(int(row[2][1:]))
      return render_template("cart_detail.html",listItems=a,imgLen=len(a),price=price,IQL=ItemQtyList)
   
   else:
      flash("Empty Cart !")
      return redirect(request.referrer)

#Rendering CART Page
@freshbasket_blueprint.route('/cart/orderdetails/<price>')
def orderConfirmation(price):
   OrderDb(dictItemsCopy,price)
   flash("Order Placed !")
   return redirect(request.referrer)

#Rendering AUTHENTICATION Page
@freshbasket_blueprint.route('/purchaseAuth' , methods=["POST","GET"])
def purchaseAuthentication():
   name=request.form.get('name')
   pno=request.form.get('pno')
   contactdetails.append(name)
   contactdetails.append(pno)
   
   global otp
   otp=getOTP(pno,name)
   
   params=dictItems 
   ItemQtyList=ItemQtyfunc(dictItemsCopy)
   ItemQtyList1=ItemQtyList.values()
   ItemQtyList1=list(ItemQtyList1)
   query='SELECT * FROM products_details WHERE product_name IN ({}) order by product_id desc'.format(','.join(['%s']*len(params)))
   cur.execute(query, params)
   data=cur.fetchall()
   
   a=[]
   price=[]
   
   for row in data:
    a.append(row)
    price.append(int(row[2][1:]))
   print(ItemQtyList)
   return render_template("auth.html",img=a,imgLen=len(a),IQL=ItemQtyList,price=price)

def getOTP(num,name):
   pno=num
   name=name
   
   account_sid=os.getenv('twilio_user')
   account_token=os.getenv('twilio_token')
   
   client = Client(account_sid,account_token)
   otpGenerate=generateOTP()
   body="Hello " + str(name) + " Your OTP is "+ str(otpGenerate)
   
   message= client.messages.create(
    from_='Twilio number',
    body=body,
    to=pno)
   return str(otpGenerate)

def paymentlink(num,name):
   pno=num
   name=name
   account_sid=os.getenv('twilio_user')
   account_token=os.getenv('twilio_token')
   client = Client(account_sid,account_token)
   body=" Hello " + str(name) + "\nTotal Amount to be paid : $"+ str(price) + "\nYour Order Summary :" + (' , \n'.join(map(str,dictItems)))
   message= client.messages.create(
    from_='Twilio Number',
    body=body,
    to=pno)
   return str(body)

def generateOTP():
    return random.randrange(100000,999999)

#OTP Validation and Confirming Purchase
@freshbasket_blueprint.route('/confirmPurchase' , methods=["POST"])
def confirmPurchase():
   global otp
   otp_user=request.form.get('pass')
   if str(otp_user)==otp:
      paymentlink(contactdetails[1],contactdetails[0])
      return f"<h1>OTP Verified , Payment Link sent to the Mobile Number</h1>"
   else:
     return redirect(url_for('.cart'))

#Order Updates in DB
def OrderDb(OrderList,Price):
   TotalPrice=(Price)
   OrderList=dict(Counter(OrderList))
   TotalItem=len(OrderList)
   TotalQty=sum(OrderList.values())
   
   cur.execute("insert into OrderTable(TotalItems,TotalQty,TotalPrice) values(%s,%s,%s)",(TotalItem,TotalQty,TotalPrice))
   con.commit()
   cur.execute("select * from OrderTable order by cartId desc limit 1")
   
   cartId=cur.fetchone()
   cartId=cartId[0]

   for key,val in OrderList.items():
    cur.execute("insert into OrderDetails values(%s,%s,%s)",(cartId,key,val))
    con.commit()
   return(OrderList,TotalQty)

def ItemQtyfunc(a):
   lisItems=dict(Counter(a))
   return lisItems
