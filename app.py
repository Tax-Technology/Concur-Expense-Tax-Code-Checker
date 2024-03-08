import streamlit as st
import pandas as pd


def parse_concur_report(data, expense_col, amount_col, tax_col, category_col, country_col, currency_col):
  """
  Parses a SAP Concur T&E report into a Pandas dataframe

  Args:
      data (pandas.DataFrame): The uploaded report data
      expense_col (str): Column name containing expense description (e.g., Hotel, Meal)
      amount_col (str): Column name containing expense amount
      tax_col (str): Column name containing tax amount
      category_col (str): Column name containing expense category
      country_col (str): Column name containing merchant country
      currency_col (str): Column name containing expense currency

  Returns:
      pandas.DataFrame: A dataframe containing parsed expense data
  """

  # Create a new dataframe to store parsed expense data
  df = pd.DataFrame({
      "Expense": data[expense_col],
      "Amount": pd.to_numeric(data[amount_col], errors='coerce'),  # Convert amount to numeric (handle errors)
      "Tax": pd.to_numeric(data[tax_col], errors='coerce'),  # Convert tax to numeric (handle errors)
      "Category": data[category_col],
      "Country": data[country_col],
      "Currency": data[currency_col]
  })

  # Drop rows with missing amount data (important for calculations)
  df.dropna(subset=["Amount"], inplace=True)

  return df


def parse_tax_config(data, code_col, rate_col, category_col, country_col):
  """
  Parses a SAP Concur tax code configuration file into a dictionary

  Args:
      data (pandas.DataFrame): The uploaded tax config data
      code_col (str): Column name containing tax code
      rate_col (str): Column name containing tax rate
      category_col (str): Column name containing expense category
      country_col (str): Column name containing merchant country

  Returns:
      dict: A dictionary mapping tax codes to tax rates for specific expense categories and countries
  """

  tax_config = {}
  for index, row in data.iterrows():
      code = row[code_col]
      rate = row[rate_col]
      category = row[category_col]
      country = row[country_col]

      # Handle missing category or country data (set to None)
      if pd.isna(category):
          category = None
      if pd.isna(country):
          country = None

      # Create a dictionary key using a tuple (category, country) for efficient lookup
      tax_config[(category, country)] = rate
  return tax_config


def analyze_vat(expense_data, tax_config):
  """
  Analyzes VAT in expense data based on tax configuration

  Args:
      expense_data (pandas.DataFrame): The parsed expense data
      tax_config (dict): The parsed tax code configuration

  Returns:
      pandas.DataFrame: A dataframe with identified VAT issues
  """

  issues = []
  for index, row in expense_data.iterrows():
      expense = row["Expense"]
      amount = row["Amount"]
      tax = row["Tax"]
      category = row["Category"]
      country = row["Country"]

      # Lookup expected tax rate based on category and country from the tax config dictionary
      expected_rate = tax_config.get((category, country))

      if expected_rate is None:
          # No matching rule found, flag missing tax code
          issues.append(f"Missing tax code for expense: {expense}")
      else:
          expected_tax = amount * expected_rate
          # Allow for minor rounding errors during calculation
          if abs(tax - expected_tax) > 0.01:
              # Flag potential tax code mismatch between expense and configuration
              issues.append(f"Potential tax code mismatch for expense: {expense}, expected tax: {expected_tax:.2f}")

  # Create a dataframe to display identified VAT issues
  return pd.DataFrame(issues, columns=["VAT Issues"])


def load_file(uploaded_file):
  """
  Loads a file based on its type (CSV, XLSX, XLS)

  Args:
      uploaded_file (streamlit.UploadedFile): The uploaded file object

  Returns:
