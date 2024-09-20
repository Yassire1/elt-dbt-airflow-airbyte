select * from {{source('destination_db','actors')}}
-- to load the actors table from the destination_db in order to be accessed by dbt