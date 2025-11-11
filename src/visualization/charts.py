# Contents of /bakerloo-line-extension/bakerloo-line-extension/src/visualization/charts.py

import matplotlib.pyplot as plt
import pandas as pd

def plot_comparative_data(data, title, xlabel, ylabel):
    """
    Generate a bar chart for comparative data.

    Parameters:
    - data: DataFrame containing the data to plot.
    - title: Title of the chart.
    - xlabel: Label for the x-axis.
    - ylabel: Label for the y-axis.
    """
    ax = data.plot(kind='bar', figsize=(10, 6))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_age_distribution(age_data, site_name):
    """
    Plot age distribution for a specific site.

    Parameters:
    - age_data: DataFrame containing age distribution data.
    - site_name: Name of the site for the title.
    """
    plot_comparative_data(age_data, f'Age Distribution for {site_name}', 'Age Groups', 'Population')

def plot_ethnicity_distribution(ethnicity_data, site_name):
    """
    Plot ethnicity distribution for a specific site.

    Parameters:
    - ethnicity_data: DataFrame containing ethnicity distribution data.
    - site_name: Name of the site for the title.
    """
    plot_comparative_data(ethnicity_data, f'Ethnicity Distribution for {site_name}', 'Ethnic Groups', 'Population')

def plot_income_distribution(income_data, site_name):
    """
    Plot income distribution for a specific site.

    Parameters:
    - income_data: DataFrame containing income distribution data.
    - site_name: Name of the site for the title.
    """
    plot_comparative_data(income_data, f'Income Distribution for {site_name}', 'Income Brackets', 'Population')

def plot_employment_distribution(employment_data, site_name):
    """
    Plot employment distribution for a specific site.

    Parameters:
    - employment_data: DataFrame containing employment distribution data.
    - site_name: Name of the site for the title.
    """
    plot_comparative_data(employment_data, f'Employment Distribution for {site_name}', 'Employment Status', 'Population')