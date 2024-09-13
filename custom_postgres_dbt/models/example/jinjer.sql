{% set film_tatle = 'Inception' %}

select * 
from {{ ref('films')}}
where title = {{film_tatle}}