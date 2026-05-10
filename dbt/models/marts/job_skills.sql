{{ config(materialized='table') }}

with exploded as (
  select job_id, jsonb_array_elements_text(job_skills) as skill
  from {{ ref('stg_jobs') }}
  where job_skills is not null
),
pairs as (
  select distinct job_id, trim(skill) as skill
  from exploded
  where skill is not null
)
select
  md5(job_id || '||' || skill) as id,
  job_id,
  md5(skill) as skill_id
from pairs
