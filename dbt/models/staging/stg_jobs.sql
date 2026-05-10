{{ config(materialized='view') }}

/*
Staging model: normalize basic fields, deduplicate by computed job_id, and cast JSON/text columns to jsonb where appropriate.
*/

with raw as (
  select *, md5(coalesce(job_title, '') || '||' || coalesce(company_name, '') || '||' || coalesce(job_posted_date::text, '')) as job_id_calc
  from {{ source('raw', 'staging_jobs') }}
),
ranked as (
  select *, row_number() over (partition by job_id_calc order by job_posted_date::timestamp desc NULLS LAST) as rn
  from raw
),
dedup as (
  select * from ranked where rn = 1
)

select
  job_id_calc as job_id,
  job_title,
  job_title_short,
  company_name,
  job_location,
  job_country,
  job_via,
  job_schedule_type,
  (case when job_work_from_home IS TRUE OR lower(coalesce(job_work_from_home::text, '')) IN ('true','t','1','yes') then true else false end) as job_work_from_home,
  job_posted_date::timestamp as job_posted_date,
  (case when job_no_degree_mention IS TRUE OR lower(coalesce(job_no_degree_mention::text, '')) IN ('true','t','1','yes') then true else false end) as job_no_degree_mention,
  (case when job_health_insurance IS TRUE OR lower(coalesce(job_health_insurance::text, '')) IN ('true','t','1','yes') then true else false end) as job_health_insurance,
  salary_rate::text as salary_rate,
  salary_year_avg::numeric as salary_year_avg,
  salary_hour_avg::numeric as salary_hour_avg,
  (case when job_skills is null then null else job_skills::jsonb end) as job_skills,
  (case when job_type_skills is null then null else job_type_skills::jsonb end) as job_type_skills,
  search_location
from dedup
