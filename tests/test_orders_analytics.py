import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.orders_analytics import (
    calculate_profit_by_order,
    calculate_most_profitable_region,
    find_most_common_ship_method,
    find_number_of_order_per_category,
    generate_analytics_reports
)

class TestOrdersAnalytics(unittest.TestCase):
    
    def setUp(self):
        """Set up test data for all tests"""
        self.test_data = pd.DataFrame({
            'Order Id': ['CA-2023-1000', 'CA-2023-1001', 'CA-2023-1002', 'CA-2023-1003'],
            'Order Date': ['2023-09-05', '2023-03-24', '2023-03-25', '2023-02-05'],
            'Ship Mode': ['Standard Class', 'First Class', 'Standard Class', 'Same Day'],
            'Segment': ['Consumer', 'Consumer', 'Home Office', 'Corporate'],
            'Country': ['United States'] * 4,
            'City': ['San Francisco', 'San Francisco', 'Fremont', 'Fremont'],
            'State': ['California', 'California', 'Nebraska', 'Nebraska'],
            'Postal Code': ['94109', '94109', '68025', '68025'],
            'Region': ['West', 'West', 'Central', 'Central'],
            'Category': ['Furniture', 'Furniture', 'Office Supplies', 'Furniture'],
            'Sub Category': ['Bookcases', 'Chairs', 'Labels', 'Tables'],
            'Product Id': ['FUR-BO-10001798', 'FUR-CH-10000454', 'OFF-LA-10000240', 'FUR-TA-10000577'],
            'cost price': [240.0, 600.0, 10.0, 780.0],
            'List Price': [260.0, 730.0, 10.0, 960.0],
            'Quantity': [2, 3, 2, 5],
            'Discount Percent': [2, 3, 5, 2]
        })
        
        # Expected profit calculations:
        # Order 1: (260 * 2 * 0.98) - (240 * 2) = 509.6 - 480 = 29.6
        # Order 2: (730 * 3 * 0.97) - (600 * 3) = 2124.3 - 1800 = 324.3
        # Order 3: (10 * 2 * 0.95) - (10 * 2) = 19 - 20 = -1
        # Order 4: (960 * 5 * 0.98) - (780 * 5) = 4704 - 3900 = 804

    def test_calculate_profit_by_order(self):
        """Test profit calculation for each order"""
        result = calculate_profit_by_order(self.test_data.copy())
        
        # Check that Profit column was added
        self.assertIn('Profit', result.columns)
        
        # Check profit calculations
        expected_profits = [29.6, 324.3, -1.0, 804.0]
        np.testing.assert_array_almost_equal(result['Profit'].values, expected_profits, decimal=1)
        
        # Check that original data is preserved
        self.assertEqual(len(result), len(self.test_data))
        self.assertIn('Order Id', result.columns)

    def test_calculate_profit_by_order_with_zero_discount(self):
        """Test profit calculation with zero discount"""
        test_data_zero_discount = self.test_data.copy()
        test_data_zero_discount['Discount Percent'] = 0
        
        result = calculate_profit_by_order(test_data_zero_discount)
        
        # Expected profits with 0% discount:
        # Order 1: (260 * 2 * 1.0) - (240 * 2) = 520 - 480 = 40
        # Order 2: (730 * 3 * 1.0) - (600 * 3) = 2190 - 1800 = 390
        # Order 3: (10 * 2 * 1.0) - (10 * 2) = 20 - 20 = 0
        # Order 4: (960 * 5 * 1.0) - (780 * 5) = 4800 - 3900 = 900
        
        expected_profits = [40.0, 390.0, 0.0, 900.0]
        np.testing.assert_array_almost_equal(result['Profit'].values, expected_profits, decimal=1)

    def test_calculate_most_profitable_region_single_max(self):
        """Test when only one region has the maximum profit"""
        # Create data where one region clearly has the highest profit
        single_max_data = pd.DataFrame({
            'Region': ['East', 'West', 'Central'],
            'cost price': [100, 100, 100],
            'List Price': [120, 120, 150],  # Central has higher profit
            'Quantity': [1, 1, 1],
            'Discount Percent': [0, 0, 0]
        })
        
        orders_with_profit = calculate_profit_by_order(single_max_data)
        result = calculate_most_profitable_region(orders_with_profit)
        
        # Should return DataFrame with only the region with maximum profit
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['Region'], 'Central')  # Central has profit of 50
        self.assertEqual(result.iloc[0]['Total_Profit'], 50.0)

    def test_calculate_most_profitable_region_equal_profits(self):
        """Test handling of regions with equal maximum profits"""
        # Create data where multiple regions have the same maximum profit
        equal_profit_data = pd.DataFrame({
            'Region': ['East', 'West', 'Central', 'South'],
            'cost price': [100, 100, 100, 200],
            'List Price': [120, 120, 120, 240],
            'Quantity': [1, 1, 1, 1],
            'Discount Percent': [0, 0, 0, 0]
        })
        
        orders_with_profit = calculate_profit_by_order(equal_profit_data)
        result = calculate_most_profitable_region(orders_with_profit)
        
        # Should return DataFrame with all regions with the maximum profit
        # East, West, Central have profit of 20 each, South has profit of 40
        # So South should be the only region with maximum profit
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)  # Only South has max profit of 40
        
        # South should be the most profitable region
        self.assertEqual(result.iloc[0]['Region'], 'South')
        self.assertEqual(result.iloc[0]['Total_Profit'], 40.0)

    def test_calculate_most_profitable_region_multiple_equal_max(self):
        """Test when multiple regions have the same maximum profit"""
        # Create data where multiple regions have exactly the same maximum profit
        equal_max_data = pd.DataFrame({
            'Region': ['East', 'West', 'Central', 'South'],
            'cost price': [100, 100, 100, 100],
            'List Price': [120, 120, 120, 110],  # All have same profit of 20
            'Quantity': [1, 1, 1, 1],
            'Discount Percent': [0, 0, 0, 0]
        })
        
        orders_with_profit = calculate_profit_by_order(equal_max_data)
        result = calculate_most_profitable_region(orders_with_profit)
        
        # Should return DataFrame with all regions having the same maximum profit
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)  # All 3 regions have max profit of 20
        
        # All profits should be equal and maximum
        profits = result['Total_Profit'].values
        self.assertTrue(all(profit == 20.0 for profit in profits))
        
        # Should include all regions with max profit
        regions = result['Region'].values
        self.assertIn('Central', regions)
        self.assertIn('East', regions)
        self.assertIn('West', regions)
        self.assertNotIn('South', regions)

    def test_calculate_most_profitable_with_negative_profits(self):
        """Test when multiple regions have the same maximum profit"""
        # Create data where all the orders have negative profits
        equal_max_data = pd.DataFrame({
            'Region': ['East', 'West', 'Central', 'South'],
            'cost price': [120, 120, 120, 120],
            'List Price': [110, 100, 100, 110], 
            'Quantity': [1, 1, 1, 1],
            'Discount Percent': [0, 0, 0, 0]
        })
        
        orders_with_profit = calculate_profit_by_order(equal_max_data)
        result = calculate_most_profitable_region(orders_with_profit)
        
        # Should return DataFrame with all regions having the same maximum profit
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # All 2 regions have max profit of -10
        
        # All profits should be equal and maximum
        profits = result['Total_Profit'].values
        self.assertTrue(all(profit == -10.0 for profit in profits))
        
        # Should include all regions with max profit
        regions = result['Region'].values
        self.assertIn('South', regions)
        self.assertIn('East', regions)
    

    def test_find_most_common_ship_method(self):
        """Test finding most common shipping method for each category"""
        result = find_most_common_ship_method(self.test_data)
        print("DEBUG: find_most_common_ship_method result:\n", result)
        
        # Should return all ship methods for Furniture (all tied, each appears once), and one for Office Supplies
        self.assertEqual(len(result), 4)  # 3 for Furniture + 1 for Office Supplies
        
        # Check that we have Category, Ship Mode, and Count columns
        self.assertIn('Category', result.columns)
        self.assertIn('Ship Mode', result.columns)
        self.assertIn('Count', result.columns)
        
        # Check Furniture category results - all ship modes should be present
        furniture_result = result[result['Category'] == 'Furniture']
        self.assertEqual(len(furniture_result), 3)  # All tied
        self.assertSetEqual(set(furniture_result['Ship Mode']), {'Standard Class', 'First Class', 'Same Day'})
        self.assertTrue(all(furniture_result['Count'] == 1))
        
        # Check Office Supplies category result
        office_supplies_result = result[result['Category'] == 'Office Supplies']
        self.assertEqual(len(office_supplies_result), 1)  # Only one option
        self.assertEqual(office_supplies_result.iloc[0]['Ship Mode'], 'Standard Class')
        self.assertEqual(office_supplies_result.iloc[0]['Count'], 1)

    def test_find_most_common_ship_method_tie(self):
        """Test handling of ties in shipping method frequency"""
        # Create data with tie in shipping methods
        tie_data = pd.DataFrame({
            'Category': ['Furniture', 'Furniture', 'Furniture', 'Furniture'],
            'Ship Mode': ['Standard Class', 'Standard Class', 'First Class', 'First Class']
        })
        
        result = find_most_common_ship_method(tie_data)
        
        # Should return both ship methods since they have the same count (2 each)
        self.assertEqual(len(result), 2)  # 2 ship methods with max count
        
        # Both should have count of 2
        counts = result['Count'].values
        self.assertTrue(all(count == 2 for count in counts))
        
        # Should include both ship methods
        ship_modes = result['Ship Mode'].values
        self.assertIn('Standard Class', ship_modes)
        self.assertIn('First Class', ship_modes)

    def test_find_most_common_ship_method_multiple_categories_tie(self):
        """Test handling of ties across multiple categories"""
        # Create data with ties in multiple categories
        multi_tie_data = pd.DataFrame({
            'Category': ['Furniture', 'Furniture', 'Furniture', 'Office Supplies', 'Office Supplies', 'Office Supplies', 'Technology'],
            'Ship Mode': ['Standard Class', 'Standard Class', 'First Class', 'Express', 'Express', 'Ground', 'Ground']
        })
        
        result = find_most_common_ship_method(multi_tie_data)
        
        # Should return 3 rows: 1 for Furniture (Standard Class), 1 for Office Supplies (Express), 1 for Technology (Ground)
        self.assertEqual(len(result), 3)
        
        # Check Furniture category has Standard Class with count 2
        furniture_results = result[result['Category'] == 'Furniture']
        self.assertEqual(len(furniture_results), 1)
        self.assertEqual(furniture_results.iloc[0]['Ship Mode'], 'Standard Class')
        self.assertEqual(furniture_results.iloc[0]['Count'], 2)
        
        # Check Office Supplies category has Express with count 2
        office_results = result[result['Category'] == 'Office Supplies']
        self.assertEqual(len(office_results), 1)
        self.assertEqual(office_results.iloc[0]['Ship Mode'], 'Express')
        self.assertEqual(office_results.iloc[0]['Count'], 2)

        # Check Technology category has Ground with count 1
        technology_results = result[result['Category'] == 'Technology']
        self.assertEqual(len(technology_results), 1)
        self.assertEqual(technology_results.iloc[0]['Ship Mode'], 'Ground')
        self.assertEqual(technology_results.iloc[0]['Count'], 1)

    def test_find_number_of_order_per_category(self):
        """Test counting orders by category and sub-category"""
        # Create test data with multiple orders for some category-subcategory combinations
        test_data = pd.DataFrame({
            'Category': ['Furniture', 'Furniture', 'Furniture', 'Furniture', 'Furniture', 
                        'Office Supplies', 'Office Supplies', 'Office Supplies', 'Technology'],
            'Sub Category': ['Bookcases', 'Bookcases', 'Chairs', 'Tables', 'Tables', 
                           'Labels', 'Labels', 'Storage', 'Phones']
        })
        
        result = find_number_of_order_per_category(test_data)
        
        # Check columns
        self.assertIn('Category', result.columns)
        self.assertIn('Sub Category', result.columns)
        self.assertIn('order_count', result.columns)
        
        # Should have 5 rows (5 unique category-subcategory combinations):
        # Furniture-Bookcases (2), Furniture-Chairs (1), Furniture-Tables (2), 
        # Office Supplies-Labels (2), Office Supplies-Storage (1), Technology-Phones (1)
        self.assertEqual(len(result), 6)
        
        # Check specific counts
        furniture_bookcases = result[(result['Category'] == 'Furniture') & 
                                   (result['Sub Category'] == 'Bookcases')]
        self.assertEqual(furniture_bookcases.iloc[0]['order_count'], 2)
        
        furniture_chairs = result[(result['Category'] == 'Furniture') & 
                                (result['Sub Category'] == 'Chairs')]
        self.assertEqual(furniture_chairs.iloc[0]['order_count'], 1)
        
        furniture_tables = result[(result['Category'] == 'Furniture') & 
                                (result['Sub Category'] == 'Tables')]
        self.assertEqual(furniture_tables.iloc[0]['order_count'], 2)
        
        office_labels = result[(result['Category'] == 'Office Supplies') & 
                             (result['Sub Category'] == 'Labels')]
        self.assertEqual(office_labels.iloc[0]['order_count'], 2)
        
        office_storage = result[(result['Category'] == 'Office Supplies') & 
                              (result['Sub Category'] == 'Storage')]
        self.assertEqual(office_storage.iloc[0]['order_count'], 1)
        
        tech_phones = result[(result['Category'] == 'Technology') & 
                           (result['Sub Category'] == 'Phones')]
        self.assertEqual(tech_phones.iloc[0]['order_count'], 1)

    def test_generate_analytics_reports(self):
        """Test the complete analytics report generation"""
        reports = generate_analytics_reports(self.test_data)
        
        # Check that all expected reports are generated
        expected_reports = ['most_profitable_region', 'most_common_ship_method', 
                           'orders_by_category', 'orders_with_profit']
        
        for report_name in expected_reports:
            self.assertIn(report_name, reports)
            self.assertIsInstance(reports[report_name], pd.DataFrame)
        
        # Check most profitable region report
        region_report = reports['most_profitable_region']
        self.assertEqual(region_report.iloc[0]['Region'], 'Central')
        self.assertAlmostEqual(region_report.iloc[0]['Total_Profit'], 803.0, places=1)
        self.assertEqual(len(region_report), 1)  # Only one region with max profit
        
        # Check orders by category report
        category_report = reports['orders_by_category']
        self.assertEqual(len(category_report), 4)  # 4 unique category-subcategory combinations

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=self.test_data.columns)
        
        # Test profit calculation
        result = calculate_profit_by_order(empty_df)
        self.assertEqual(len(result), 0)
        self.assertIn('Profit', result.columns)
        
        # Test most profitable region with empty DataFrame
        # Should return empty DataFrame instead of raising exception
        region_result = calculate_most_profitable_region(result)
        self.assertIsInstance(region_result, pd.DataFrame)
        self.assertEqual(len(region_result), 0)
        
        # Test ship method analysis
        result = find_most_common_ship_method(empty_df)
        self.assertEqual(len(result), 0)
        
        # Test category counting
        result = find_number_of_order_per_category(empty_df)
        self.assertEqual(len(result), 0)

    def test_missing_columns(self):
        """Test handling of missing required columns"""
        incomplete_data = self.test_data.drop(columns=['cost price', 'List Price'])
        
        with self.assertRaises(KeyError):
            calculate_profit_by_order(incomplete_data)

    def test_numeric_data_types(self):
        """Test that numeric calculations work with different data types"""
        # Convert numeric columns to different types
        test_data_mixed_types = self.test_data.copy()
        test_data_mixed_types['cost price'] = test_data_mixed_types['cost price'].astype(float)
        test_data_mixed_types['List Price'] = test_data_mixed_types['List Price'].astype(int)
        test_data_mixed_types['Quantity'] = test_data_mixed_types['Quantity'].astype(float)
        test_data_mixed_types['Discount Percent'] = test_data_mixed_types['Discount Percent'].astype(int)
        
        # Should still work correctly
        result = calculate_profit_by_order(test_data_mixed_types)
        self.assertIn('Profit', result.columns)
        self.assertEqual(len(result), len(test_data_mixed_types))

if __name__ == '__main__':
    unittest.main() 