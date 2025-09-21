import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

#streamlit keeps rerunning this script anu time changes happen
# open up termila and run    streamlit run main.py
# then it should open a local host on google chrome called "localhost:8501"

st.set_page_config(
    page_title="Simple Finance App", 
    page_icon="💸",
    layout="wide"
    )

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized" : []
    }

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():
            details = str(row["Details"]).lower()  # make sure it's a string
            for keyword in lowered_keywords:
                if keyword in details:  # string match
                    df.at[idx, "Category"] = category
                    break

    return df

def load_transactions(file):
    try:
        df = pd.read_csv(file)
        # grab all cols in the dataframe (the first row of the csv file)
        # remove trailing or leading white spaces (good practice)
        df.columns = [col.strip() for col in df.columns]
        # if my bank uses value, use value instead of ammount
        df["Amount"] = df["Amount"].astype(str).str.replace(",", "").astype(float) #panda operation
        df["Date"] = pd.to_datetime(df["Date"], format = "%d %b %Y") #day, name of month, year

    
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None
    

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    
    return False



def main():
    st.title("Simple Finance Dashboard")

    # command in streamlit
    uploaded_file = st.file_uploader("Upload your transaction CSV file", type=["csv"])

    # did we upload a file
    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            st.session_state.debits_df = debits_df.copy()

            #now set up debit and credit tabs
            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details" , "Amount" , "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format= "%.2f CAD"), #change to CAD if using RBC
                        "Category": st.column_config.SelectboxColumn(
                            "Category", options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if row["Category"] == st.session_state.debits_df.at[idx, "Category"]:
                            continue  #if no change in row we can continue

                        # if chnage in row
                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)


                st.subheader('Expense Summary')
                category_totals = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f CAD") #chnage to CAD
                    },
                    use_container_width=True,
                    hide_index=True
                             )
                


                # plotly express figures
                fig = px.pie(
                    category_totals,
                    values = "Amount",
                    names = "Category",
                    title = "Expenses by Category",
                )
                st.plotly_chart(fig, use_container_width=True) #takes up entire width of screen

                fig2 = px.bar(
                    category_totals,
                    x="Category",
                    y="Amount",
                    title="Expenses by Category (Bar Chart)",
                    text_auto=True,
                )

                fig2.update_traces(
                    texttemplate="%{y:,.2f}",   # format with commas + 2 decimals
                    textposition="outside"      # put labels above bars
                )

                
                st.plotly_chart(fig2, use_container_width=True)


            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} CAD") #Change to CAD
                st.write(credits_df)




main()