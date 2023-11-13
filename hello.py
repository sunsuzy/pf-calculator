import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, number_of_colors):
    setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
    deco_price_from_qty = selected_print['decoPriceFromQty'].values
    deco_price = selected_print['decoPrice'].values

    selected_print = selected_print.sort_values(by='decoPriceFromQty')

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

def main():
    st.title("PF Pricing Calculator")

    # Replace the URL with the correct one for the new file
    product_price_feed_df = pd.read_csv("https://github.com/sunsuzy/pf-calculator/blob/cba9eb342ecc1b7aa1d3c29b23f85437a4071734/product_price_feed.csv", delimiter='\t', dtype={'nettPriceQ1': 'object'}, low_memory=False)
    print_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv", delimiter=';', low_memory=False)

    product_price_feed_df['nettPriceQ1'] = product_price_feed_df['nettPriceQ1'].apply(convert_nett_price)
    product_price_feed_df['priceBar'] = product_price_feed_df['priceBar'].apply(pd.to_numeric, errors='coerce')

    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    if query:  # If the query is not empty
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].astype(str).str.lower() == str(query).lower()]
        if not matched_items.empty:
            descriptions = [matched_items['description'].values[0]]
        else:  # Otherwise, treat it as a product description
            closest_matches = process.extract(query, descriptions, limit=10)
            descriptions = [match[0] for match in closest_matches]
    else:
        descriptions = []
    description = st.selectbox('Select a product', descriptions)
    
    matched_products = product_price_feed_df[product_price_feed_df['description'] == description]
    if not matched_products.empty:
        item_code = matched_products['itemcode'].values[0]
        st.write(f"Item Code: {item_code}")

        selected_product = product_price_feed_df[product_price_feed_df['itemcode'] == item_code].copy()

        available_print_techniques = selected_product['decoCharge'].values[0].split(',')
        print_techniques_with_names = []
        for technique in available_print_techniques:
            technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
            if not technique_df.empty:
                print_techniques_with_names.append((technique, technique_df['impMethod'].values[0]))
        print_technique = st.selectbox('Select a print technique', options=print_techniques_with_names, format_func=lambda x: f"{x[0]} - {x[1]}")

        selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == print_technique[0]]

        available_colors = selected_print_technique['amountColorsId'].unique()
        available_colors = [str(color) for color in available_colors]
        print_colors = st.selectbox('Enter the number of print colors', available_colors)

        # Find the minimum quantity that has a price available
        min_quantity_from_price_bar = int(selected_product[selected_product['nettPriceQ1'].notnull()]['priceBar'].min())

        quantity = st.number_input('Enter quantity', min_value=min_quantity_from_price_bar)

        selected_product['priceBar'] = selected_product['priceBar'].astype(int)

        applicable_price_bar = selected_product[selected_product['priceBar'] <= quantity]['priceBar'].max()
        applicable_nett_price_df = selected_product.loc[selected_product['priceBar'] == applicable_price_bar, 'nettPriceQ1']
        if not applicable_nett_price_df.empty:
            applicable_nett_price = applicable_nett_price_df.values[0]
        else:
            st.error('No matching product found for the given price bar.')
            return

        total_product_cost = quantity * applicable_nett_price

        selected_print = selected_print_technique[selected_print_technique['amountColorsId'] == print_colors]

        if print_colors == "Full color":
            number_of_colors = None
        else:
            number_of_colors = int(print_colors)

        total_print_cost = calculate_total_print_cost(selected_print, quantity, number_of_colors)

        total_cost_excl_shipping = total_product_cost + total_print_cost
        shipping_cost = 18 if total_product_cost < 620 else 0
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
        st.write('No matching products found.')

if __name__ == "__main__":
    main()
