import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, num_colors=None, logo_size=None):
    setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
    price_dependence = selected_print.iloc[0]['priceDependence']

    if price_dependence == 'none':
        deco_price = convert_nett_price(selected_print['decoPrice'].values[0])
    elif price_dependence == 'colors':
        deco_price = convert_nett_price(selected_print[selected_print['amountColorsId'].astype(str) == str(num_colors)]['decoPrice'].values[0])
    elif price_dependence == 'size':
        deco_price = convert_nett_price(selected_print[selected_print['logoSizeCm2'] == logo_size]['decoPrice'].values[0])

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
    product_price_feed_df['nettPrice'] = product_price_feed_df['nettPrice'].apply(convert_nett_price)
    product_price_feed_df['priceBar'] = product_price_feed_df['priceBar'].apply(pd.to_numeric, errors='coerce')
    return product_price_feed_df

def display_available_print_techniques(selected_product, print_price_feed_df):
    available_print_techniques = selected_product['decoCharge'].split(',')
    print_techniques_with_names_and_dependence = []
    for technique in available_print_techniques:
        technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
        if not technique_df.empty:
            price_dependence = technique_df['priceDependence'].values[0]
            print_techniques_with_names_and_dependence.append((technique, technique_df['impMethod'].values[0], price_dependence))
    return print_techniques_with_names_and_dependence

def get_size_options(selected_print_technique):
    size_options = selected_print_technique['logoSizeCm2'].unique()
    return sorted([str(size) for size in size_options])

# Main function
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

            print_techniques_with_names_and_dependence = display_available_print_techniques(selected_product, print_price_feed_df)

            selected_technique_info = st.selectbox(
                'Select a print technique',
                options=print_techniques_with_names_and_dependence,
                format_func=lambda x: f"{x[1]} ({x[0]}) - {x[2]}"
            )
            selected_technique, price_dependence = selected_technique_info[0], selected_technique_info[2]

            selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == selected_technique]

            num_colors, logo_size = None, None
            if price_dependence == 'Colors':
                available_colors = selected_print_technique['amountColorsId'].unique()
                num_colors = st.selectbox('Select the number of print colors', options=available_colors)
            elif price_dependence == 'Size':
                size_options = get_size_options(selected_print_technique)
                logo_size = st.selectbox('Select the print size (cm²)', options=size_options)
                logo_size = float(logo_size)  # Convert selected size back to float for comparison

            min_quantity_from_price_bar = int(selected_product[selected_product['nettPrice'].notnull()]['priceBar'].min())
            quantity = st.number_input('Enter quantity', min_value=min_quantity_from_price_bar)

            total_print_cost = calculate_total_print_cost(selected_print_technique, quantity, num_colors, logo_size)

            # Display total print cost
            st.write(f"Total print cost: €{total_print_cost:.2f}")

            # Further logic for calculating and displaying other costs can follow here

if __name__ == "__main__":
    main()
