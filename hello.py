import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, num_colors):
    # This function might need adjustment based on available data
    try:
        setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
        deco_price = convert_nett_price(selected_print[selected_print['amountColorsId'].astype(str) == str(num_colors)]['decoPrice'].values[0])
        total_print_cost = setup_charge + (deco_price * quantity)
        return total_print_cost
    except IndexError:  # Handling cases where a specific color count is not available
        return 0

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

def calculate_and_display_all_costs(selected_product, quantity, decorations_info):
    # Calculate product cost
    applicable_price_bar = selected_product[selected_product['priceBar'] <= quantity]['priceBar'].max()
    applicable_nett_price_df = selected_product.loc[selected_product['priceBar'] == applicable_price_bar, 'nettPrice']
    if not applicable_nett_price_df.empty:
        applicable_nett_price = applicable_nett_price_df.values[0]
        total_product_cost = quantity * applicable_nett_price
    else:
        total_product_cost = 0  # Handle case with no applicable price
    
    # Calculate total decoration cost
    total_decoration_cost = sum([info['cost'] for info in decorations_info])
    
    # Assuming shipping or other additional costs logic here
    shipping_cost = 13 if (total_product_cost + total_decoration_cost) < 620 else 0
    
    # Total cost
    total_cost_incl_shipping = total_product_cost + total_decoration_cost + shipping_cost
    
    # Displaying the costs
    st.write(f"Total product cost: €{total_product_cost:.2f}")
    st.write(f"Total decoration cost: €{total_decoration_cost:.2f}")
    st.write(f"Shipping cost: €{shipping_cost:.2f}")
    st.write(f"Total cost including shipping: €{total_cost_incl_shipping:.2f}")

def get_technique_color_options(print_price_feed_df, technique, selected_product):
    """
    Filters available color options based on the selected print technique and product.
    """
    technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
    # Filter based on what's applicable to the selected product, if necessary
    color_options = technique_df['amountColorsId'].unique()
    return sorted(set(color_options))  # Return sorted unique color options

def main():
    st.title("PF Pricing Calculator")
    product_price_feed_df, print_price_feed_df = load_data()

    if product_price_feed_df is None or print_price_feed_df is None:
        return

    product_price_feed_df = preprocess_data(product_price_feed_df)
    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')

    if query:
        # Product search and selection logic...
        # Assuming product selection logic is implemented here...
    selected_techniques = st.multiselect('Select print techniques', options=available_print_techniques, format_func=lambda x: f"{x[0]} - {x[1]}")

    decorations_info = []
    for technique, name in selected_techniques:
        color_options = get_technique_color_options(print_price_feed_df, technique, selected_product)
        if not color_options:
            st.write(f"No color options available for {name}.")
            continue
        selected_color = st.selectbox(f'Number of colors for {name}', options=color_options, key=f"colors_{technique}")
        num_colors = int(selected_color)  # Assuming color options are stored as integers or can be converted
        cost = calculate_total_print_cost(print_price_feed_df[print_price_feed_df['printCode'] == technique], quantity, num_colors)
        decorations_info.append({'technique': technique, 'num_colors': num_colors, 'cost': cost})

    # Assuming quantity input and other logic remains the same...
    quantity = st.number_input('Enter quantity', min_value=1, key="quantity")

    # Call the function to calculate and display all costs
    calculate_and_display_all_costs(selected_product, quantity, decorations_info)

if __name__ == "__main__":
    main()
