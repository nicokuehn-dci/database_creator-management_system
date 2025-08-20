# Data Analytics & Visualization Guide

This guide explains how to use the data analytics and visualization features in Database Creator to analyze your data and create insightful visualizations.

## Overview

The Data Analytics tab provides a complete environment for:
- Running SQL queries against your databases
- Viewing and analyzing query results
- Creating various visualizations and charts
- Exporting visualizations for reports or presentations

## Getting Started

### Connecting to a Database

1. Open the Data Analytics tab in the Database Creator application
2. In the "Database Connection" section, select a database from the dropdown menu
3. The connection info will show details about the selected database

You can connect to:
- SQLite databases in your database storage folder
- External databases (MySQL, PostgreSQL, SQL Server, Oracle) that have been configured

### Writing and Running Queries

1. Enter your SQL query in the query editor
2. Use the "Sample queries" dropdown to load example queries for common tasks
3. Click "Run Query" to execute your query
4. View the results in the "Query Results" section

#### Query Tips

- Use `LIMIT` to restrict the number of rows returned for better performance
- Avoid `SELECT *` for large tables; select only the columns you need
- For visualizations, focus on queries that produce numerical results for analysis
- Use column aliases (`AS`) to make column names more readable in visualizations

## Working with Results

Query results are displayed in three different views:

### Data Grid

The Data Grid shows your query results in a tabular format:
- Scroll horizontally and vertically to see all data
- Column headers show the column names from your query
- Results are displayed in a structured table similar to spreadsheet software

### Raw Data

The Raw Data view shows the query results as formatted text:
- Useful for copying and pasting data
- Fixed-width format makes it easy to read
- Shows all data in a single text view

### Statistics

The Statistics view provides summary information about your query results:
- Dataset overview (rows, columns)
- Column types and data structures
- Numerical statistics (mean, median, min, max, etc.)
- Distribution information for categorical columns
- Missing value analysis

## Creating Visualizations

### Available Chart Types

1. **Bar Chart** - Compare values across categories
2. **Line Chart** - Show trends over time or sequences
3. **Pie Chart** - Display proportions of a whole
4. **Scatter Plot** - Examine relationships between two variables
5. **Histogram** - View distribution of a single variable
6. **Box Plot** - Analyze statistical distribution and outliers
7. **Heat Map** - Visualize patterns and correlations in complex data

### Creating a Chart

1. Run a query that returns data appropriate for visualization
2. Select a chart type from the dropdown menu
3. Choose the columns to use for X-axis and Y-axis
   - X-axis typically represents categories or independent variables
   - Y-axis typically represents values or dependent variables
4. Click "Generate Visualization" to create the chart

### Saving Charts

1. Create and refine your visualization
2. Click "Save Chart" to export it
3. Choose a format (PNG, PDF, SVG, JPEG)
4. Select a location to save the file

## Example Queries

### Basic Data Exploration

```sql
-- Get the first 100 records from a table
SELECT * FROM customers LIMIT 100;
```

### Aggregation and Grouping

```sql
-- Count records by category
SELECT 
    category,
    COUNT(*) as count
FROM 
    products
GROUP BY 
    category
ORDER BY 
    count DESC;
```

### Time-based Analysis

```sql
-- Monthly sales analysis
SELECT 
    strftime('%Y-%m', order_date) as month,
    SUM(total_amount) as monthly_revenue,
    COUNT(*) as order_count,
    AVG(total_amount) as average_order
FROM 
    orders
WHERE 
    order_date >= date('now', '-1 year')
GROUP BY 
    month
ORDER BY 
    month;
```

### Join and Analyze

```sql
-- Customer purchase analysis
SELECT 
    c.customer_name,
    c.city,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as average_order
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
GROUP BY 
    c.customer_id
ORDER BY 
    total_spent DESC
LIMIT 
    20;
```

## Working with External Databases

When connecting to external databases:

1. Make sure the required drivers are installed
2. Configure the connection in the Database Management tab first
3. External databases appear in the dropdown with their type (e.g., [MYSQL] Database)

### Notes for Specific Database Types

#### MySQL
- Supports standard SQL with some MySQL-specific functions
- Date formatting uses `DATE_FORMAT()` instead of `strftime()`

#### PostgreSQL
- Case-sensitive object names (tables, columns)
- Rich set of data types and functions
- Use `to_char()` for date formatting

#### SQL Server
- Use `CONVERT()` or `FORMAT()` for date formatting
- Top N queries use `SELECT TOP N` syntax

#### Oracle
- Use `TO_CHAR()` for date formatting
- Dual table for queries without a table reference

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify connection details (host, port, username, password)
   - Check that the database server is running
   - Ensure network connectivity to the database server

2. **Query Error**
   - Check SQL syntax
   - Verify table and column names
   - Confirm you have permission to access the objects

3. **Visualization Issues**
   - Ensure appropriate data types for the selected chart type
   - For time series, make sure date/time values are properly formatted
   - For categorical charts, limit the number of categories (group smaller ones if needed)

4. **Performance Issues**
   - Add appropriate WHERE clauses to limit data
   - Use LIMIT to restrict result set size
   - For large databases, consider creating targeted views or indices
