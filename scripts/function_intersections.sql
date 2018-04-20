CREATE OR REPLACE FUNCTION get_intersect(roads_a TEXT [], roads_b TEXT [], OUT result JSONB)
LANGUAGE plpgsql
AS $$
DECLARE
  intersetions TEXT[];
BEGIN
  SELECT array_agg(DISTINCT st_geometryn(st_intersection(t1, t2),1)) INTO intersetions
  FROM unnest(roads_a) t1, unnest(roads_b) t2
  WHERE NOT st_isempty(st_intersection(t1, t2));
  SELECT json_agg(json_build_object('lat', st_y(t3), 'lon', st_x(t3))) INTO result
  FROM unnest(intersetions) t3;
  EXCEPTION
  WHEN OTHERS
    THEN
      result := SQLERRM;
END
$$;
