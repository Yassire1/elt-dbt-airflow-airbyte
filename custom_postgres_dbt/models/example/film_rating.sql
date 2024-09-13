with films_with_rating as (
    select 
        film_id,
        title,
        release_date,
        price,
        rating,
        user_rating,
        CASE 
            WHEN user_rating >= 4.5 THEN 'Excellent'
            WHEN user_rating >= 4.0 THEN 'Good'
            WHEN user_rating >= 3.0 THEN 'Average'
            ELSE 'Poor'
        END as rating_category
    from {{ ref('films') }}

),

films_with_actors as (
    select
        f.film_id,
        f.title,
        STRING_AGG(a.actor_name, ',') AS actors
    from {{ ref('films') }} f
    LEFT JOIN {{ ref('film_actors') }} fa ON f.film_id = fa.film_id
    LEFT JOIN {{ ref('actors') }} a ON fa.actor_id = a.actor_id
    GROUP BY f.film_id, f.title
)

select
    fwf.*,
    fwa.actors
from films_with_rating fwf
LEFT JOIN films_with_actors fwa ON fwf.film_id = fwa.film_id
