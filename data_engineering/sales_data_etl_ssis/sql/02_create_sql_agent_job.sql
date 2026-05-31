/*
 * Creates a nightly SQL Server Agent job that executes the SSIS package
 * SalesDataETL. Adjust @ssisdb_path / @schedule_frequency to taste.
 *
 * Prereqs:
 *   - The package has been deployed to the SSIS Catalog (SSISDB) under
 *     the folder/project given below.
 *   - SQL Server Agent service is running.
 *   - SSISDB is enabled on this instance.
 *
 * Usage:
 *   sqlcmd -S <server> -E -i sql/02_create_sql_agent_job.sql
 */

USE msdb;
GO

DECLARE
    @job_name       SYSNAME = N'SalesDataETL_Nightly',
    @ssisdb_folder  NVARCHAR(128) = N'SalesDataETL_Project',
    @ssisdb_project NVARCHAR(128) = N'sales_data_etl_ssis',
    @package_name   NVARCHAR(260) = N'SalesDataETL.dtsx';

-- Idempotent: drop the job if it already exists so re-runs don't fail.
IF EXISTS (SELECT 1 FROM dbo.sysjobs WHERE name = @job_name)
    EXEC dbo.sp_delete_job @job_name = @job_name, @delete_unused_schedule = 1;

DECLARE @job_id UNIQUEIDENTIFIER;
EXEC dbo.sp_add_job
    @job_name = @job_name,
    @enabled = 1,
    @description = N'Nightly Sales CSV -> SQL Server ETL via SSIS.',
    @job_id = @job_id OUTPUT;

EXEC dbo.sp_add_jobserver @job_id = @job_id;

DECLARE @command NVARCHAR(MAX) =
    N'/ISSERVER "\"\SSISDB\' + @ssisdb_folder + N'\' + @ssisdb_project + N'\' + @package_name + N'\""';

EXEC dbo.sp_add_jobstep
    @job_id = @job_id,
    @step_name = N'Run SSIS package',
    @subsystem = N'SSIS',
    @command = @command,
    @on_success_action = 1,  -- quit reporting success
    @on_fail_action = 2;     -- quit reporting failure

EXEC dbo.sp_add_schedule
    @schedule_name = N'SalesDataETL_Daily_0200',
    @freq_type = 4,           -- daily
    @freq_interval = 1,
    @active_start_time = 020000;

EXEC dbo.sp_attach_schedule
    @job_id = @job_id,
    @schedule_name = N'SalesDataETL_Daily_0200';

GO
