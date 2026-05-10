{{ config(materialized='table') }}

select distinct
  md5(coalesce(company_name, '')) as company_id,
  company_name
from {{ ref('stg_jobs') }}
where company_name is not null
