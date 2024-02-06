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
        matched_items = product_price_feed_df[(product_price_feed_df['itemcode'].str.lower() == query.lower()) | (product_price_feed_df['description'].str.lower().str.contains(query.lower()))]
        if not matched_items.empty:
            description = st.selectbox('Select a product', matched_items['description'].unique())
            selected_product = matched_items[matched_items['description'] == description].iloc[0]

            # Ensure selected_product is accessed correctly
            st.write(f"Item Code: {selected_product['itemcode']}")

            print_techniques_with_names_and_dependence = display_available_print_techniques(selected_product, print_price_feed_df)
            if print_techniques_with_names_and_dependence:
                selected_technique_info = st.selectbox(
                    'Select a print technique',
                    options=print_techniques_with_names_and_dependence,
                    format_func=lambda x: f"{x[1]} ({x[0]}) - {x[2]}"
                )
                selected_technique, _, price_dependence = selected_technique_info

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

                        # Assume product_cost, shipping_cost, and additional_fees are calculated or retrieved
            product_cost = quantity * applicable_nett_price  # Example; already calculated
            shipping_cost = 0  # Placeholder for shipping cost logic
            if total_print_cost + product_cost < 620:
                shipping_cost = 13  # Example shipping logic based on order value

            additional_fees = 0  # Placeholder for any additional fees

            total_cost = product_cost + total_print_cost + shipping_cost + additional_fees

            # Displaying cost breakdown
            st.write(f"Product cost: €{product_cost:.2f}")
            st.write(f"Print cost: €{total_print_cost:.2f}")
            st.write(f"Shipping cost: €{shipping_cost:.2f}")
            st.write(f"Additional fees: €{additional_fees:.2f}")
            st.write(f"**Total cost: €{total_cost:.2f}**")

if __name__ == "__main__":
    main()
