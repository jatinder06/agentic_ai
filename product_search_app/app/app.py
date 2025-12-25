import streamlit as st
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT_ASSIGNMENT")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

print("Environment variables set for LangChain and Groq.", os.environ.items())


# ---------------------
# Define Pydantic schema
# ---------------------



class Product(BaseModel):
    product_name: str = Field(description="Name of the product")
    brand: str = Field(description="Brand of the product")
    model: str = Field(description="Model of the product")
    specs: str = Field(description="Specifications of the product")
    price: str = Field(description="Price of the product")
    link: str = Field(description="URL link to the product")

# ---------------------
# LangChain setup
# ---------------------
model = ChatGroq(model="qwen-qwq-32b", temperature=0.0)
output_parser = JsonOutputParser(pydantic_object=Product)

# Create the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an ecommerce search engine assistant who searches for requested products."),
       ("user", "Answer the user query strictly in the following valid JSON format without think text:\n{format_instructions}\nQuery: {query}"),
    ]
).partial(format_instructions=output_parser.get_format_instructions())  # Pass format instructions


chat = prompt | model | output_parser

# ---------------------
# Streamlit UI
# ---------------------
st.title("🛒 E-commerce Product Search")
st.markdown(
    """
    <style>
        .main-title {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }
        .query-input {
            margin-top: 20px;
            text-align: center;
        }
        .product-card {
            border: 2px solid #ddd;
            border-radius: 12px;
            padding: 20px;
            background-color: var(--background-color);
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }
        .product-card p {
            font-size: 16px;
            margin: 5px 0;
            color: var(--text-color);
        }
        .product-card a {
            color: #4CAF50;
            text-decoration: none;
            font-weight: bold;
        }
        :root {
            --background-color: #ffffff; /* Default light mode */
            --text-color: #000000; /* Default light mode */
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #333333; /* Dark mode background */
                --text-color: #ffffff; /* Dark mode text */
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

query = st.text_input("Enter a product query:", "Find best mobile phone deal", key="query")

if st.button("Search"):
    with st.spinner("Searching..."):
        try:
            response = chat.invoke({"query": query})
            print(response)
            st.subheader("Product Found")
            st.markdown(
                f"""
                <div class="product-card">
                    <p><strong>Product Name:</strong> {response.product_name or 'N/A'}</p>
                    <p><strong>Brand:</strong> {response.brand or 'N/A'}</p>
                    <p><strong>Model:</strong> {response.model or 'N/A'}</p>
                    <p><strong>Specifications:</strong> {response.specs or 'N/A'}</p>
                    <p><strong>Price:</strong> {response.price or 'N/A'}</p>
                    <p><strong>🔗 <a href="{response.link or '#'}" target="_blank">Product Link</a></strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Error: {e}")
# ---------------------

## Find best mobile phone deal
## Find best laptop deal
## find the best Mutual Fund for investment
## Find best TV deal
## Find the best  pair of shoes