"""Product & Category Sales page."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data_loader import load_orders, load_products
from src.metrics import category_sales, product_sales
from src.utils import format_currency

st.set_page_config(page_title="Product Sales", page_icon="🛍️", layout="wide")
st.title("🛍️ Product & Category Sales")
st.caption("What sells, and which categories carry the revenue.")

orders, products = load_orders(), load_products()
cats = category_sales(orders, products)
prods = product_sales(orders, products)

top_cat = cats.iloc[0]
top_prod = prods.iloc[0]
c = st.columns(3)
c[0].metric("Top category", top_cat["category"], f"{top_cat['revenue_share_%']:.1f}% of revenue")
c[1].metric("Top product", top_prod["product_name"], format_currency(top_prod["revenue"]))
c[2].metric("Products sold", f"{int(prods['units'].sum()):,}")

st.divider()
left, right = st.columns(2)

fig_cat = px.pie(
    cats, values="revenue", names="category", template="plotly_white",
    title="Revenue share by category", hole=0.45,
)
left.plotly_chart(fig_cat, use_container_width=True)

top10 = prods.head(10).sort_values("revenue")
fig_top = px.bar(
    top10, x="revenue", y="product_name", orientation="h", template="plotly_white",
    title="Top 10 products by revenue", labels={"revenue": "Revenue ($)", "product_name": ""},
)
fig_top.update_traces(marker_color="#0ea5e9")
right.plotly_chart(fig_top, use_container_width=True)

st.divider()
st.subheader("Category scorecard")
cat_disp = cats.copy()
cat_disp["revenue"] = cat_disp["revenue"].map(format_currency)
st.dataframe(
    cat_disp.rename(columns={"category": "Category", "revenue": "Revenue", "units": "Units",
                             "orders": "Orders", "revenue_share_%": "Revenue %"}),
    use_container_width=True, hide_index=True,
)

st.subheader("All products")
prod_disp = prods.copy()
prod_disp["revenue"] = prod_disp["revenue"].map(format_currency)
st.dataframe(
    prod_disp.rename(columns={"product_name": "Product", "category": "Category",
                              "revenue": "Revenue", "units": "Units", "orders": "Orders"}),
    use_container_width=True, hide_index=True,
)
