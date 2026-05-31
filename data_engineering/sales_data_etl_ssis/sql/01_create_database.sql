/*
 * Creates SalesDataDB and the target SalesData table that the SSIS package
 * (and the Python reference ETL) load into.
 *
 * Run once before importing/executing SalesDataETL.dtsx.
 *
 * Usage:
 *   sqlcmd -S <server> -E -i sql/01_create_database.sql
 */

IF DB_ID(N'SalesDataDB') IS NULL
BEGIN
    CREATE DATABASE SalesDataDB;
END
GO

USE SalesDataDB;
GO

IF OBJECT_ID(N'dbo.SalesData', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SalesData
    (
        OrderID       INT            NOT NULL PRIMARY KEY,
        OrderDate     DATETIME2(0)   NOT NULL,
        CustomerID    INT            NOT NULL,
        ProductID     INT            NOT NULL,
        ProductName   NVARCHAR(100)  NOT NULL,
        Quantity      INT            NOT NULL CHECK (Quantity > 0),
        UnitPrice     DECIMAL(18,2)  NOT NULL CHECK (UnitPrice >= 0),
        TotalPrice    DECIMAL(18,2)  NOT NULL CHECK (TotalPrice >= 0),
        IngestedAt    DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE INDEX IX_SalesData_OrderDate ON dbo.SalesData(OrderDate);
    CREATE INDEX IX_SalesData_CustomerID ON dbo.SalesData(CustomerID);
END
GO

IF OBJECT_ID(N'dbo.SalesData_ErrorLog', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SalesData_ErrorLog
    (
        ErrorLogID    INT            IDENTITY(1,1) PRIMARY KEY,
        OrderID       VARCHAR(50)    NULL,
        RawRow        NVARCHAR(MAX)  NOT NULL,
        ErrorCode     INT            NULL,
        ErrorColumn   INT            NULL,
        ErrorMessage  NVARCHAR(MAX)  NULL,
        LoggedAt      DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF OBJECT_ID(N'dbo.SalesData_RunLog', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SalesData_RunLog
    (
        RunID         INT            IDENTITY(1,1) PRIMARY KEY,
        RunAt         DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
        SourceFile    NVARCHAR(500)  NOT NULL,
        RowsRead      INT            NOT NULL,
        RowsWritten   INT            NOT NULL,
        RowsRejected  INT            NOT NULL,
        DurationMs    INT            NOT NULL
    );
END
GO
