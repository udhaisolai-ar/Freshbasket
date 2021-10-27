import pandas as pd
import pymysql
from datetime import datetime
import random
import os
from dotenv import *

load_dotenv()
db_Password=os.getenv('dbp')
db_User=os.getenv('dbU')
db=os.getenv('db')

#DB connection
con=pymysql.connect(host='localhost',user=db_User,password=db_Password,db=db)
cur=con.cursor()

#Seasonal Products for Recommendation 
Summer=['mango','watermelon','blackberry','blueberry','cantaloupe','cherry','peach']
Spring=['cherry','mango','peach']
Autumn=['apple','kiwi','grapes']
Winter=['grapefruit','blueberry','kiwi']

def getseason(season):
    if season>2 and season<=4:
        f=Spring
    elif season>5 and season<=8:
        f=Summer
    elif season>8 and season<=11:
        f=Autumn
    else:
        f=Winter
    return f

#Retrieving Data from SQL
orders = pd.read_sql("select * from orderdetails",con)

def recommendation(item,season):
    
    f=getseason(season)
    
    #Order ID's of orders containing item
    product_order = orders[orders.ProductName == item].cartId.unique()

    #Filtering Products bought together
    relevant_orders = orders[orders.cartId.isin(product_order)]
    similar_products = relevant_orders[relevant_orders.ProductName != item]

    #No of occurence of similar products 
    No_similar_products = similar_products.groupby("ProductName")["ProductName"].count().reset_index(name="No of occurence")
    
    #size of order's containing given item(input) 
    Num_product_order = product_order.size

    #converting to a dataFrame
    product_instances = pd.DataFrame(No_similar_products)
    
    #Seasonal Items Picker
    s=[]    
    for i in f:
        if i!=item:
            s2=[]
            s2.append(i)
            t=product_instances['No of occurence'][product_instances['ProductName']==i]
            print(t)
            s2.append(t.iloc[0])
            print(s2)
            s.append(s2)
    s=sorted(s,reverse=True,key=lambda a:a[1])

    #recommended items
    recommended_products = pd.DataFrame(product_instances.sort_values("No of occurence", ascending=False).head(3))
    recommended_products=list(recommended_products["ProductName"])

    for i in s:
        if i[0] not in recommended_products and len(recommended_products)<4:
            recommended_products.append(i[0])
    return recommended_products


