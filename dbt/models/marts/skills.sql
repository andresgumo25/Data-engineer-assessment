{{ config(materialized='table') }}

with exploded as (
  select distinct jsonb_array_elements_text(job_skills) as skill
  from {{ ref('stg_jobs') }}
  where job_skills is not null
)
select
  md5(skill) as skill_id,
  skill
from exploded
where skill is not null
