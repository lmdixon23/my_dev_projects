# Sales Data ETL SSIS

## Overview

**Sales_Data_ETL_SSIS** is a structured ETL (Extract, Transform, Load) process built using SQL Server Integration Services (SSIS). This project extracts sales data from a CSV file, applies necessary data transformations, and loads the cleaned data into a SQL Server database for further analysis. The process includes error handling, logging, and automation to ensure data integrity and smooth execution.

## Key Features

- **Data Extraction**: The package extracts sales data from a CSV file stored in a file system, acting as a simple data lake.
- **Data Transformation**: The data undergoes various transformations such as data type conversions (e.g., string to DateTime, numeric conversions) and validation.
- **Error Handling**: Redirects error rows during transformation and logs the details for further inspection, ensuring that failed records are captured.
- **Row Count Logging**: A row count transformation is included to log the number of successfully processed rows.
- **Automated Execution**: The package is set up to run automatically at regular intervals using SQL Server Agent, ensuring ongoing data updates without manual intervention.
- **Performance Considerations**: Optimized for batch inserts to the database, with logging and error handling to avoid performance bottlenecks.

## Example Usage

After running the SSIS package, the following operations are executed:

- **Extract**: Data is extracted from the `sales_data.csv` file.
- **Transform**: Data is converted, validated, and cleaned using the **Convert_SalesDataTypes** task.
- **Load**: The transformed data is loaded into the `SalesData` table in the `SalesDataDB` SQL Server database.
- **Error Handling**: Any rows that fail transformation are logged in a separate file for review.

## Future Enhancements

- **Additional Data Validations**: Add further validation checks to improve data quality before loading into the database.
- **Scaling for Larger Datasets**: Implement partitioning and parallelism to handle larger datasets.
- **Data Enrichment**: Include additional data sources for enrichment, such as product information or customer demographics.

## Technical Specifications

- **Tool**: SQL Server Integration Services (SSIS)
- **Source**: CSV file (`sales_data.csv`)
- **Destination**: SQL Server database (`SalesDataDB`)
- **Error Handling**: Redirected error rows and logging
- **Automation**: Scheduled execution via SQL Server Agent

## Contributing

Contributions to enhance the ETL process, performance, or error handling are welcome. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries, please contact lmdixon23@gmail.com.

## Getting Started

### Prerequisites

- **SQL Server**: Ensure you have SQL Server installed, along with SQL Server Management Studio (SSMS) to manage the database.
- **SQL Server Integration Services (SSIS)**: Ensure SSIS is installed and configured within your SQL Server instance.
- **Visual Studio**: Required to develop and manage the SSIS package.

### Installation

1. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects/data_engineering_projects/sales_data_etl_ssis.git
cd sales_data_etl_ssis
```

2. Import the SSIS package (SalesDataETL.dtsx) into SQL Server Data Tools (SSDT) or Visual Studio.

3. Configure the connection strings in the Connection Manager to point to your SQL Server instance.

4. Run the package to extract, transform, and load the sales data.

5. Optionally, schedule the package in SQL Server Agent for automated execution.