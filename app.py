import streamlit as st
import pandas as pd


def parse_concur_report(data, expense_col, amount_col, tax_col, category_col, country_col, currency_col):
    df = pd.DataFrame({
        "Expense": data[expense_col],
        "Amount": pd.to_numeric(data[amount_col], errors='coerce'),
        "Tax": pd.to_numeric(data[tax_col], errors='coerce'),
        "Category": data[category_col],
        "Country": data[country_col],
        "Currency": data[currency_col]
    })
    df.dropna(subset=["Amount"], inplace=True)
    return df


def parse_tax_config(data, code_col, rate_col, category_col, country_col):
    tax_config = {}
    for _, row in data.iterrows():
        code = row[code_col]
        rate = row[rate_col]
        category = row[category_col] if not pd.isna(row[category_col]) else None
        country = row[country_col] if not pd.isna(row[country_col]) else None

        tax_config[(category, country)] = rate
    return tax_config


def analyze_vat(expense_data, tax_config):
    issues = []
    for _, row in expense_data.iterrows():
        expense = row["Expense"]
        amount = row["Amount"]
        tax = row["Tax"]
        category = row["Category"]
        country = row["Country"]

        expected_rate = tax_config.get((category, country))

        if expected_rate is None:
            issues.append(f"Missing tax code for expense: {expense}")
        else:
            expected_tax = amount * expected_rate
            if abs(tax - expected_tax) > 0.01:
                issues.append(f"Potential tax code mismatch for expense: {expense}, expected tax: {expected_tax:.2f}")

    return pd.DataFrame(issues, columns=["VAT Issues"])


def load_file(uploaded_file):
    try:
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            else:
                st.error("Unsupported file type. Please upload a CSV or Excel file.")
                return None

            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None
