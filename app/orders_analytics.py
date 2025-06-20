import pandas as pd
"Complete thes functions or write your own to perform the following tasks"

def calculate_profit_by_order(orders_df):
    """
    Calculate profit for each order in the DataFrame
    Profit = (List Price * Quantity * (1 - Discount Percent/100)) - (Cost Price * Quantity)
    """
    # Calculate revenue after discount
    revenue = orders_df['List Price'] * orders_df['Quantity'] * (1 - orders_df['Discount Percent'] / 100)
    
    # Calculate total cost
    total_cost = orders_df['cost price'] * orders_df['Quantity']
    
    # Calculate profit
    profit = revenue - total_cost
    
    # Add profit column to DataFrame
    orders_df['Profit'] = profit
    
    return orders_df

def calculate_most_profitable_region(orders_with_profit):
    """
    Calculate the most profitable region(s) and their profit
    Returns: DataFrame with columns ['Region', 'Total_Profit'] for regions with maximum profit
    """
    # Group by region and sum profits
    region_profits = orders_with_profit.groupby('Region')['Profit'].sum()
    
    # Find the maximum profit
    max_profit = region_profits.max()
    
    # Get all regions with the maximum profit incase there's more than one region with the same max profit
    most_profitable_regions = [(region, profit) for region, profit in region_profits.items() if profit == max_profit]
    
    # Sort by region name for consistent ordering in case of ties
    most_profitable_regions.sort(key=lambda x: x[0])
    
    # Convert to DataFrame
    result_df = pd.DataFrame(most_profitable_regions, columns=['Region', 'Total_Profit'])
    
    return result_df

def find_most_common_ship_method(orders_df):
    """
    Find the most common shipping method(s) for each Category.
    Returns: DataFrame with Category, Ship Mode, and Count.
    If multiple ship methods have the same maximum frequency, all are returned.
    """
    if orders_df.empty:
        return pd.DataFrame(columns=['Category', 'Ship Mode', 'Count'])
    # Group by Category and Ship Mode, count occurrences
    ship_method_counts = orders_df.groupby(['Category', 'Ship Mode']).size().reset_index(name='Count')

    # For each category, find the maximum count
    result_rows = []
    for category, group in ship_method_counts.groupby('Category'):
        max_count = group['Count'].max()
        most_common = group[group['Count'] == max_count]
        result_rows.append(most_common)
    if not result_rows:
        return pd.DataFrame(columns=['Category', 'Ship Mode', 'Count'])
    result_df = pd.concat(result_rows, ignore_index=True)
    result_df = result_df.sort_values(['Category', 'Ship Mode']).reset_index(drop=True)
    return result_df

def find_number_of_order_per_category(orders_df):
    """
    Find the number of orders for each Category and Sub Category
    Returns: DataFrame with Category, Sub Category, and order count
    """
    # Group by Category and Sub Category, count orders
    category_order_counts = orders_df.groupby(['Category', 'Sub Category']).size().reset_index(name='order_count')
    
    return category_order_counts

def generate_analytics_reports(orders_df):
    """
    Generate all analytics reports and return them as DataFrames
    Returns: dictionary containing all analytics reports
    """
    reports = {}
    
    # 1. Orders with profit calculation
    orders_with_profit = calculate_profit_by_order(orders_df)
    reports['orders_with_profit'] = orders_with_profit

    # 2. Most profitable region
    region_profits = calculate_most_profitable_region(orders_with_profit)
    reports['most_profitable_region'] = region_profits
    
    # 3. Most common shipping method for each category
    reports['most_common_ship_method'] = find_most_common_ship_method(orders_df)
    
    # 4. Number of orders by category and sub-category
    reports['orders_by_category'] = find_number_of_order_per_category(orders_df)
    
    return reports
