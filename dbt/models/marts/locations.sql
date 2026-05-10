{{ config(materialized='table') }}

select distinct
  md5(coalesce(job_location, '')) as location_id,
  job_location as location_string,
  job_country
from {{ ref('stg_jobs') }}
where job_location is not null
