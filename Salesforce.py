import streamlit as st
import pandas as pd
from simple_salesforce import Salesforce
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# ---------------------- Salesforce Connection ----------------------
from simple_salesforce import Salesforce

sf = Salesforce(
    username='',
    password='',
    security_token=''
)


# ---------------------- Gemini (LangChain) Setup ----------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    google_api_key=""
)

prompt = PromptTemplate(
    input_variables=["question"],
    template="""You are a helpful, friendly customer support chatbot.
Answer the following customer question clearly and politely:

Customer: {question}
Support Bot:"""
)

chain = LLMChain(llm=llm, prompt=prompt)

# ---------------------- Salesforce Functions ----------------------
def fetch_product_details(product_name):
    query = f"""
    SELECT Id, Name, Product_Name__c, Price_c__c, Category__c, Rating__c
    FROM Product__c
    WHERE Name = '{product_name}'
    """
    result = sf.query(query)
    records = result['records']
    if not records:
        return "❌ No product found with that name!"
    df = pd.DataFrame(records).drop(columns='attributes')
    return df

def update_product_price(product_name, new_price):
    query = f"SELECT Id FROM Product__c WHERE Name = '{product_name}'"
    result = sf.query(query)
    records = result['records']
    if not records:
        return "❌ No product found to update!"
    product_id = records[0]['Id']
    sf.Product__c.update(product_id, {'Price_c__c': new_price})
    return f"✅ Updated {product_name}'s price to ₹{new_price}"

def create_product(name, product_name, price, category, rating):
    try:
        sf.Product__c.create({
            'Name': name,
            'Product_Name__c': product_name,
            'Price_c__c': float(price),
            'Category__c': category,
            'Rating__c': float(rating)
        })
        return f"✅ Product '{name}' created successfully!"
    except Exception as e:
        return f"❌ Error creating product: {str(e)}"

def customer_support_response(question):
    result = chain.run(question=question)
    return result

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="Salesforce Chatbot", layout="centered")
st.title("🤖 Salesforce Product Chatbot")

menu = st.sidebar.selectbox("Choose an Option", [
    "Fetch Product Details",
    "Update Product Price",
    "Create Product",
    "Customer Support"
])

# ---- FETCH PRODUCT DETAILS ----
if menu == "Fetch Product Details":
    st.subheader("🔍 Fetch Product Info")
    product_name = st.text_input("Enter Product Name:")
    if st.button("Get Details"):
        result = fetch_product_details(product_name)
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.error(result)

# ---- UPDATE PRODUCT PRICE ----
elif menu == "Update Product Price":
    st.subheader("💰 Update Product Price")
    product_name = st.text_input("Enter Product Name:")
    new_price = st.text_input("Enter New Price:")
    if st.button("Update Price"):
        if product_name and new_price:
            try:
                result = update_product_price(product_name, float(new_price))
                st.success(result)
            except ValueError:
                st.error("Please enter a valid number for the price.")
        else:
            st.warning("Please fill in both fields.")

# ---- CREATE PRODUCT ----
elif menu == "Create Product":
    st.subheader("🆕 Create New Product")
    name = st.text_input("Salesforce Record Name (Unique):")
    product_name = st.text_input("Product Name:")
    price = st.text_input("Price:")
    category = st.text_input("Category:")
    rating = st.text_input("Rating:")

    if st.button("Create Product"):
        if name and product_name and price and category and rating:
            try:
                result = create_product(name, product_name, price, category, rating)
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
            except Exception as e:
                st.error(f"Unexpected error: {e}")
        else:
            st.warning("Please fill all the fields.")

# ---- CUSTOMER SUPPORT ----
elif menu == "Customer Support":
    st.subheader("🧠 Ask Your Question")
    question = st.text_area("Ask a customer support question:")
    if st.button("Get Response"):
        if question.strip():
            response = customer_support_response(question)
            st.info(response)
        else:
            st.warning("Please enter a question.")
