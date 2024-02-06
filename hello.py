import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity):
    setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
    deco_price_from_qty = selected_print['decoPriceFromQty'].values
    deco_price = selected_print['decoPrice'].values

    applicable_deco_price_from_qty = None
    applicable_deco_price = None

    for i in range(len(deco_price_from_qty)):
        if quantity >= int(deco_price_from_qty[i]):
            applicable_deco_price_from_qty = int(deco_price_from_qty[i])
            applicable_deco_price = convert_nett_price(deco_price[i])
        else:
            break

    if applicable_deco_price_from_qty is None:
        applicable_deco_price_from_qty = int(deco_price_from_qty[-1])
        applicable_deco_price = convert_nett_price(deco_price[-1])

    total_print_cost = setup_charge + quantity * applicable_deco_price
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

def display_available_print_techniques(selected_product, print_price_feed_df):
    available_print_techniques = selected_product['decoCharge'].values[0].split(',')
    print_techniques_with_names = []
    for technique in available_print_techniques:
        technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
        if not technique_df.empty:
            print_techniques_with_names.append((technique, technique_df['impMethod'].values[0]))
    selected_technique = st.selectbox('Select a print technique', options=print_techniques_with_names, format_func=lambda x: f"{x[0]} - {x[1]}")
    return selected_technique

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

            print_technique = display_available_print_techniques(selected_product, print_price_feed_df)

            selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == print_technique[0]]
            selected_print_technique = selected_print_technique.sort_values(by='decoPriceFromQty')
            
            available_colors = selected_print_technique['amountColorsId'].unique()
            print_colors = st.selectbox('Enter the number of print colors', [str(color) for color in available_colors])

            min_quantity_from_price_bar = int(selected_product[selected_product['nettPrice'].notnull()]['priceBar'].min())
            quantity = st.number_input('Enter quantity', min_value=min_quantity_from_price_bar)

            applicable_price_bar = selected_product[selected_product['priceBar'] <= quantity]['priceBar'].max()
            applicable_nett_price_df = selected_product.loc[selected_product['priceBar'] == applicable_price_bar, 'nettPrice']
            if not applicable_nett_price_df.empty:
                applicable_nett_price = applicable_nett_price_df.values[0]
                total_product_cost = quantity * applicable_nett_price

                selected_print = selected_print_technique[selected_print_technique['amountColorsId'] == print_colors]
                total_print_cost = calculate_total_print_cost(selected_print, quantity)

                total_cost_excl_shipping = total_product_cost + total_print_cost
                shipping_cost = 13 if total_cost_excl_shipping < 620 else 0
                total_cost_incl_shipping = total_cost_excl_shipping + shipping_cost

                kostprijs = total_cost_incl_shipping / quantity
                margin = st.slider('Enter margin (0-100)', min_value=0, max_value=100, value=38)
                sell_price = kostprijs / (1 - (margin / 100))

                cost_breakdown_data = {
                    'Cost Component': ['Productkosten', 'Decoratiekosten (inclusief setup)', 'Totaal excl. verzending', 'Verzendkosten', 'Totaal'],
                    'Amount': [total_product_cost, total_print_cost, total_cost_excl_shipping, shipping_cost, total_cost_incl_shipping]
                }
                cost_breakdown_df = pd.DataFrame(cost_breakdown_data)
                cost_breakdown_df['Amount'] = cost_breakdown_df['Amount'].apply(lambda x: '€ {:.2f}'.format(x))

                st.write('Kostenoverzicht:')
                st.table(cost_breakdown_df)

                st.markdown(f"<p style='color:red'>**Kostprijs: € {kostprijs:.2f}**</p>", unsafe_allow_html=True)
                st.markdown(f"**Verkoopprijs: € {sell_price:.2f}**")
            else:
                st.error('No matching product found for the given price bar.')
        else:
            st.write('No matching products found.')

if __name__ == "__main__":
    main()
