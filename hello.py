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
    price_dependence = selected_print['priceDependence'].values[0]

    if price_dependence == 'none':
        deco_price = convert_nett_price(selected_print['decoPrice'].values[0])
    elif price_dependence == 'colors':
        deco_price = convert_nett_price(selected_print[selected_print['amountColorsId'] == num_colors]['decoPrice'].values[0])
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
    print_techniques_with_names = []
    for technique in available_print_techniques:
        technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
        if not technique_df.empty:
            print_techniques_with_names.append((technique, technique_df['impMethod'].values[0]))
    return print_techniques_with_names

def get_size_options(selected_print):
    size_options = selected_print['logoSizeCm2'].unique()
    return sorted(size_options)

def main():
    st.title("PF Pricing Calculator")

    product_price_feed_df, print_price_feed_df = load_data()
    if product_price_feed_df is None or print_price_feed_df is None:
        return
    
    product_price_feed_df = preprocess_data(product_price_feed_df)
    
    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    
    if query:
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].str.contains(query, case=False) | product_price_feed_df['description'].str.contains(query, case=False)]
        if not matched_items.empty:
            description = st.selectbox('Select a product', matched_items['description'].unique())
            selected_product = matched_items[matched_items['description'] == description].iloc[0]
            st.write(f"Item Code: {selected_product['itemcode']}")

            print_techniques_with_names = display_available_print_techniques(selected_product, print_price_feed_df)
            selected_technique_info = st.selectbox('Select a print technique', options=print_techniques_with_names, format_func=lambda x: f"{x[1]} ({x[0]})")
            selected_technique = selected_technique_info[0]

            selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == selected_technique]
            price_dependence = selected_print_technique['priceDependence'].values[0]

            num_colors = None
            logo_size = None
            if price_dependence == 'colors':
                available_colors = selected_print_technique['amountColorsId'].unique()
                num_colors = st.selectbox('Select the number of print colors', options=available_colors)
            elif price_dependence == 'size':
                size_options = get_size_options(selected_print_technique)
                size_option = st.selectbox('Select the print size', options=size_options)
                logo_size = size_option  # assuming logoSizeCm2 is a direct match for size_option

            min_quantity_from_price_bar = int(selected_product['priceBar'].min())
            quantity = st.number_input('Enter quantity', min_value=min_quantity_from_price_bar, value=min_quantity_from_price_bar)

            total_print_cost = calculate_total_print_cost(selected_print_technique, quantity, num_colors, logo_size)

            # Display total print cost
            st.write(f"Total print cost: €{total_print_cost:.2f}")
            
            # Further code to calculate and display product cost and any additional costs goes here...

            # Calculate and display final cost including shipping, margins, etc.
            # ...

        else:
            st.write("No matching products found.")

if __name__ == "__main__":
    main()


