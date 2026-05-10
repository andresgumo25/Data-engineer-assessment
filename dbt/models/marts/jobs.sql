{{ config(materialized='table') }}

select
  job_id,
  job_title,
  job_title_short,
  md5(coalesce(company_name, '')) as company_id,
  md5(coalesce(job_location, '')) as location_id,
  job_via,
  job_schedule_type,
  job_work_from_home,
  job_posted_date,
  job_no_degree_mention,
  job_health_insurance,
  salary_rate,
  salary_year_avg,
  salary_hour_avg,
  search_location
from {{ ref('stg_jobs') }}
