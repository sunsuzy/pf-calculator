import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, num_colors):
    setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
    deco_price = convert_nett_price(selected_print[selected_print['amountColorsId'] == str(num_colors)]['decoPrice'].values[0])
    total_print_cost = setup_charge + (deco_price * quantity)
    return total_print_cost

def load_data():
    try:
        product_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/product_price_feed.csv", delimiter=',', dtype={'priceBar': 'str', 'nettPrice': 'object'}, low_memory=False)
        print_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv", delimiter=',', low_memory=False)
        return product_price_feed_df, print_price_feed_df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None, None

def preprocess_data(product_price_feed_df):
    if product_price_feed_df is not None:
        product_price_feed_df['nettPrice'] = product_price_feed_df['nettPrice'].apply(convert_nett_price)
        product_price_feed_df['priceBar'] = product_price_feed_df['priceBar'].apply(pd.to_numeric, errors='coerce')
    return product_price_feed_df

def get_available_print_techniques(selected_product, print_price_feed_df):
    available_print_techniques = selected_product['decoCharge'].values[0].split(',')
    print_techniques_with_names = []
    for technique in available_print_techniques:
        technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
        if not technique_df.empty:
            print_techniques_with_names.append((technique, technique_df['impMethod'].values[0]))
    return print_techniques_with_names

def main():
    st.title("PF Pricing Calculator")

    product_price_feed_df, print_price_feed_df = load_data()
    if product_price_feed_df is None or print_price_feed_df is None:
        return

    product_price_feed_df = preprocess_data(product_price_feed_df)

    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    if query:
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].astype(str).str.lower() == query.lower()]
        if not matched_items.empty:
            descriptions = [matched_items['description'].values[0]]
        else:
            closest_matches = process.extract(query, descriptions, limit=10)
            descriptions = [match[0] for match in closest_matches]
    else:
        descriptions = []

    if descriptions:
        description = st.selectbox('Select a product', descriptions)
        matched_products = product_price_feed_df[product_price_feed_df['description'] == description]
        if not matched_products.empty:
            item_code = matched_products['itemcode'].values[0]
            st.write(f"Item Code: {item_code}")

            selected_product = product_price_feed_df[product_price_feed_df['itemcode'] == item_code].copy()
            selected_product['priceBar'] = selected_product['priceBar'].fillna(0)
            selected_product['priceBar'] = pd.to_numeric(selected_product['priceBar'], errors='coerce').astype(int)

            available_print_techniques = get_available_print_techniques(selected_product, print_price_feed_df)
            selected_techniques = st.multiselect('Select print techniques', options=available_print_techniques, format_func=lambda x: f"{x[0]} - {x[1]}")

            total_decoration_cost = 0
            decorations_info = []
            for technique, name in selected_techniques:
                st.write(f"Details for {name}:")
                num_colors = st.number_input(f'Enter the number of print colors for {name}', min_value=1, key=f"num_colors_{technique}")
                selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == technique]
                decorations_info.append((technique, num_colors, selected_print_technique))

            quantity = st.number_input('Enter quantity', min_value=1, key="quantity")

            for technique, num_colors, selected_print_technique in decorations_info:
                total_decoration_cost += calculate_total_print_cost(selected_print_technique, quantity, num_colors)

            # Assuming price and cost calculations for the product itself remain unchanged
            # Here you would calculate and display the total product cost, including the decoration cost

            st.write(f"Total decoration cost: €{total_decoration_cost:.2f}")
            # Further calculations and displays as needed

if __name__ == "__main__":
    main()
